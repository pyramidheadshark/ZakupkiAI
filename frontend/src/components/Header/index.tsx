import { useState } from 'react'
import './style.scss'

function Header() {


  return (
    <div id="Header">
        <div className="logo">
            <img src="../../../public/logo.svg" alt="" />
            <span>
              <span className='exo'>
                <span className='name'>РУА</span>
                    — ваш личный чат бот
              </span>
            </span>
        </div>
    </div>
  )
}

export default Header