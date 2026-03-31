/**
 * Provider-agnostic LLM API caller.
 * Supports: Anthropic, Google Gemini
 *
 * @param {object} opts
 * @param {string} opts.provider   - 'anthropic' | 'gemini'
 * @param {string} opts.modelId    - model id for the provider
 * @param {string} opts.apiKey     - API key for the provider
 * @param {string} opts.prompt     - user prompt text
 * @param {number} [opts.maxTokens=2048]
 * @returns {Promise<string>} extracted text from the LLM response
 */
export async function callLlm({ provider, modelId, apiKey, prompt, maxTokens = 2048 }) {
  if (provider === 'gemini') {
    const url = `/api/gemini/v1beta/models/${modelId}:generateContent?key=${apiKey}`
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { maxOutputTokens: maxTokens }
      })
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.error?.message || `Gemini error ${response.status}`)
    }
    const data = await response.json()
    const candidate = data.candidates?.[0]
    const text = candidate?.content?.parts?.map(p => p.text || '').join('') ?? ''
    
    if (candidate?.finishReason && candidate.finishReason !== 'STOP') {
      throw new Error(`Generación bloqueada o interrumpida por la IA (Razón de API: ${candidate.finishReason}).\n\nContenido parcial:\n${text}`)
    }
    return text;
  }

  if (provider === 'moonshot') {
    const response = await fetch('/api/moonshot/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: modelId,
        max_tokens: maxTokens,
        messages: [{ role: 'user', content: prompt }]
      })
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.error?.message || `Moonshot error ${response.status}`)
    }
    const data = await response.json()
    return data.choices?.[0]?.message?.content ?? ''
  }

  if (provider === 'groq') {
    const response = await fetch('/api/groq/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: modelId,
        max_tokens: maxTokens,
        messages: [{ role: 'user', content: prompt }]
      })
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.error?.message || `Groq error ${response.status}`)
    }
    const data = await response.json()
    return data.choices?.[0]?.message?.content ?? ''
  }

  // Default: Anthropic
  const response = await fetch('/api/anthropic/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true'
    },
    body: JSON.stringify({
      model: modelId,
      max_tokens: maxTokens,
      messages: [{ role: 'user', content: prompt }]
    })
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.error?.message || `Anthropic error ${response.status}`)
  }
  const data = await response.json()
  const text = data.content?.[0]?.text ?? ''
  
  if (data.stop_reason && data.stop_reason !== 'end_turn') {
    throw new Error(`Generación bloqueada o interrumpida por Anthropic (Razón de API: ${data.stop_reason}).\n\nContenido parcial:\n${text}`)
  }
  return text;
}
