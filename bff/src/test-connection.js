async function test(url) {
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(id);
    console.log(`URL: ${url}`);
    console.log(`Status: ${res.status}`);
    console.log(`OK: ${res.ok}`);
    try {
      const text = await res.text();
      console.log(`Body snippet: ${text.substring(0, 150)}`);
    } catch(e) {
      console.log('No body');
    }
  } catch (err) {
    console.log(`URL: ${url}`);
    console.log(`Error Message: ${err.message}`);
  }
  console.log('---');
}

async function run() {
  console.log('Testing CubeJS endpoints...\n');
  await test('http://127.0.0.1:4000/readyz');
  await test('http://127.0.0.1:4000/cubejs-api/v1/meta');
  await test('http://localhost:4000/readyz');
  await test('http://localhost:4000/cubejs-api/v1/meta');
  await test('http://cubejs.pm.comsatel.com.pe:4000/readyz');
  await test('http://cubejs.pm.comsatel.com.pe:4000/cubejs-api/v1/meta');
  await test('http://cubejs.pm.comsatel.com.pe/readyz');
  await test('http://cubejs.pm.comsatel.com.pe/cubejs-api/v1/meta');
}

run();
