import './style.scss'
import MyMessage from './MyMessage'
import BotMessage from './BotMessage'
import { useSelector } from 'react-redux'
import { RootState } from '../../../store/redusers/chatSlice'

function Messages() {
  const {msgs} = useSelector((store:RootState) => store.chat)
    
  return (
    <div id="Messages">
        {msgs.map((msg, i) => msg.who === "me" 
            ? <MyMessage key={i} msg={msg}/> 
            : <BotMessage key={i} msg={msg}/>
        )}
    </div>
  )
}

export default Messages;