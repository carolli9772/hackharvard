require("dotenv").config();
const WebSocket = require("ws");

const API_KEY = process.env.AISSTREAM_API_KEY;
const url = "wss://stream.aisstream.io/v0/stream";

const ws = new WebSocket(url, { handshakeTimeout: 15000 });

ws.on("open", () => {
  const subscribeMsg = {
    ApiKey: API_KEY,
    BoundingBoxes: [
      [-90, -180],
      [90, 180],
    ],
  };
  ws.send(JSON.stringify(subscribeMsg));
  console.log("connected, subscription sent");
});

ws.on("message", (data) => {
  try {
    const msg = JSON.parse(data.toString());
    // handle message: msg will contain AIS data (position, MMSI, voyage, etc.)
    console.log("message", msg);
  } catch (e) {
    console.error("non-json message", e);
  }
});

ws.on("error", (err) => console.error("ws error", err));
ws.on("close", (code, reason) => console.log("closed", code, reason));
