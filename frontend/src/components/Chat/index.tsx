import { useEffect, useState } from 'react'
import './style.scss'
import InputMessage from './InputMessage'
import Messages from './Messages'

function Chat() {

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
            <Messages/>
            <InputMessage/>
          </>
        :
          <>
            <InputMessage/>
            <Messages/>
          </>
      }
    </div>
  )
}

export default Chat
