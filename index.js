const axios = require("axios");
const express = require("express");
const CORS = require("cors");

const app = express();

app.use(CORS());
app.use(express.json());



app.post("/bot", async (req, res) => {
    const inputText = req.body.text;

    try{
        const response = await axios.post("http://localhost:5000/process_text",{
            input_text: inputText
        });

        const answerText = response.data.status;
        res.send({ msg: answerText });
        console.log("Отправка запроса: ", answerText);

    } catch (e) {
        console.log("Ошибка при отправке данных", e);
        res.status(500).send({error: 'Ошибка на питоне'});
    }
});


app.listen(3000, () => console.log("http://localhost:3000"));
