async function run() {
  const url = "http://127.0.0.1:8000/api/kline/2330";
  const res = await fetch(url);
  const rows = await res.json();

  console.log("len:", rows.length);
  console.log("last row keys:", Object.keys(rows[rows.length - 1]));
  console.log("last row sample:", rows[rows.length - 1]);
}

run();
