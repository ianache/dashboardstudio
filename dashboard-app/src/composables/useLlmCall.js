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
    return data.candidates?.[0]?.content?.parts?.[0]?.text ?? ''
  }

  // Default: Anthropic
  const response = await fetch('/api/anthropic/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
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
  return data.content?.[0]?.text ?? ''
}
