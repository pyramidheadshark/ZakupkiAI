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
            ? <MyMessage key={msg.who+msg.time+i} msg={msg}/> 
            : <BotMessage key={msg.who+msg.time+i} msg={msg}/>
        )}
    </div>
  )
}

export default Messages;