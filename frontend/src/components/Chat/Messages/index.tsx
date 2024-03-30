import './style.scss'
import MyMessage from './MyMessage'
import BotMessage from './BotMessage'

interface Msg{
  who: "me" | "bot"
  msg: string
}

interface Props{
  msgs: Msg[]
}

function Messages({msgs}: Props) {


  return (
    <div id="Messages">
        {msgs.map((msg, i) => msg.who === "me" 
            ? <MyMessage key={i}>{msg.msg}</MyMessage> 
            : <BotMessage key={i}>{msg.msg}</BotMessage>
        )}
    </div>
  )
}

export default Messages;