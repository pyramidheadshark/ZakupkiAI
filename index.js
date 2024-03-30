// const { NlpManager } = require("node-nlp");
const express = require("express");
const CORS = require("cors");
// const manager = new NlpManager({ languages: ["ru"] });

const app = express();

app.use(CORS());
app.use(express.json());

// manager.addDocument('ru', 'Привет', 'Здрасьте');
// manager.addDocument('ru', 'Прив', 'Здрасьте');
// manager.addDocument('ru', 'Хелло', 'Здрасьте');
// manager.addDocument('ru', 'Утречко', 'Здрасьте');
// manager.addDocument('ru', 'Хаюхай', 'Здрасьте');

// manager.addAnswer('ru', 'Привет', 'Хай')
// manager.addAnswer('ru', 'Привет', 'хелки')
// manager.addAnswer('ru', 'Привет', 'ПРивет')
// manager.addAnswer('ru', 'Привет', 'ЙО чуваак')

// manager.train().then(async () => {
// manager.save();
app.get("/", (req, res) => {
  res.send("HI asd");
});

app.post("/bot", async (req, res) => {
  // let response = await manager.process('ru', req.query.message);
  // res.send(response.answer || 'Напиши нормально');
  console.log(req.body); //тут принимаем
  res.send({ msg: "tut response" }); //тут отдаем
});

app.listen(3000, () => console.log("http://localhost:3000"));
// });
