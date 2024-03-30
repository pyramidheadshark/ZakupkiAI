import { useState } from 'react'
import './style.scss'
import { textPush } from '../../../http/API'

interface Msg{
  who: "me" | "bot"
  msg: string
}

interface Props{
  setMsgs:React.Dispatch<React.SetStateAction<Msg[]>>
}
function InputMessage({setMsgs}:Props) {

  const [inputText, setInputText] = useState('')
  
  async function sendMessage() {
    setMsgs(msgs => [...msgs, {who: "me", msg: inputText}])
    setMsgs(msgs => [...msgs, {who: "bot", msg: "..."}])
    // const response: string = await textPush(inputText)
    // setMsgs(msgs => [...msgs, {who: "bot", msg: response}])
  }

  return (
    <div id="InputMessage" className="InputMessage">
      <input type="text" value={inputText} onChange={e => setInputText(e.target.value)}   placeholder='Введите ваш запрос' />
      <div>
        <select className='exo2' name="" id="">
          <option>44-ФЗ</option>
          <option>223-ФЗ</option>
        </select>
        <button onClick={sendMessage}>
          <img src="../../../public/ic_search_white.svg" alt="" />
          <span>
            Отправить
          </span>
        </button>
      </div>
    </div>
  )
}

export default InputMessage
