import { useEffect, useState } from 'react'
import './style.scss'
import InputMessage from './InputMessage'
import Messages from './Messages'

function Chat() {
  interface Msg{
    who: "me" | "bot"
    msg: string
  }

  const [msgs, setMsgs] = useState<Msg[]>([])
  const [windowWidth, setWindowWidth] = useState(window.innerWidth)

  useEffect(() => {
    function handleResize() {
      setWindowWidth(window.innerWidth)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [window.innerWidth])

  return (
    <div id="Chat">
      {windowWidth < 587 
        ?
          <>        
            <Messages msgs={msgs}/>
            <InputMessage setMsgs={setMsgs}/>
          </>
        :
          <>
            <InputMessage setMsgs={setMsgs}/>
            <Messages msgs={msgs}/>
          </>
      }

    </div>
  )
}

export default Chat
