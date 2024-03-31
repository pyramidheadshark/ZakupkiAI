import { useState } from 'react'
import './style.scss'
import { textPush } from '../../../http/API'
import { useDispatch } from 'react-redux'
import { setMsgs } from '../../../store/redusers/chatSlice'

interface Msg{
  who: "me" | "bot"
  msg: string
}


function InputMessage() {

  const [inputText, setInputText] = useState('')
  const dispatch = useDispatch()

  async function sendMessage() {
   
    const date = new Date(Date.now())
    dispatch(setMsgs({who: "me", msg: inputText, time: date.getHours() + ":" + date.getMinutes()}))
    dispatch(setMsgs({who: "bot", msg: "...", time: date.getHours() + ":" + date.getMinutes()}))

    const federalLaw: HTMLSelectElement = document.querySelector('#federalLaw')!
    const response = await textPush(inputText, federalLaw.value)
    console.log(response)

    await textPush(inputText, federalLaw.value).then((response) => {
      const date = new Date(Date.now())
      setTimeout(() => {
        dispatch(setMsgs({who: "bot", msg: response.msg as string, time: date.getHours() + ":" + date.getMinutes()}))
      }, 1000 *60)
      dispatch(setMsgs({who: "bot", msg: response.msg as string, time: date.getHours() + ":" + date.getMinutes()}))
    })
  }

  return (
    <div id="InputMessage" className="InputMessage">
      <input type="text" value={inputText} onChange={e => setInputText(e.target.value)}   placeholder='Введите ваш запрос' />
      <div>
        <select id='federalLaw' className='exo2'>
          <option>44-ФЗ</option>
          <option>223-ФЗ</option>
        </select>
        <button className='exo2' onClick={sendMessage}>
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
