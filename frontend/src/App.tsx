import { useState } from 'react'
import './App.scss'
import Chat from './components/Chat'
import LinksOn from './components/LinksOn'
import Header from './components/Header'

function App() {


  return (
    <>
      <Header />
      <div id="App">
        <Chat />
        <LinksOn />
      </div>
    </>
  )
}

export default App
