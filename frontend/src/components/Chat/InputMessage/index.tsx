import { useState } from 'react'
import './style.scss'
import { useDispatch } from 'react-redux'
import { fetchPush, setMsgs } from '../../../store/redusers/chatSlice'
import { AppDispatch } from '../../../store'

function InputMessage() {

  const [inputText, setInputText] = useState('')
  const dispatch = useDispatch<AppDispatch>()

  async function sendMessage() { 
    const date = new Date(Date.now())
    const federalLaw: HTMLSelectElement = document.querySelector('#federalLaw')!
    const time = date.getHours() + ":" + date.getMinutes()

    dispatch(setMsgs(
      {
        Msg:{
          who: "me", 
          msg: inputText, 
          time, 
          status: "sent"
        }, 
        federalLaw: federalLaw.value
      }))
     dispatch(fetchPush({text: inputText, federalLaw: federalLaw.value}));
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
