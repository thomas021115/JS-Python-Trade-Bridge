async function run() {
  const res = await fetch("http://127.0.0.1:8000/api/ai-briefing/2330");
  const data = await res.json();
  console.log(data);
}

run();
