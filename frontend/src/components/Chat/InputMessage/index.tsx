import { useState } from 'react'
import './style.scss'

function InputMessage() {


  return (
    <div id="InputMessage" className="InputMessage">
      <input  placeholder='Введите ваш запрос' />
      <div>
        <select className='exo2' name="" id="">
          <option>44-ФЗ</option>
        </select>
        <button>
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
