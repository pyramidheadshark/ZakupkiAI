import './style.scss'
import logo from "../../../../../public/icon_rua.svg"
import MsgInfo from '../MsgInfo'
import { Msg } from '../../../../Interfaces/Msg'
interface Props{
  msg: Msg
}

function BotMessage({msg}: Props) {
  return (
    <div className="BotMessage exo">
        <img src={logo} alt="" />
        <MsgInfo msg={msg} />
    </div>
  )
}

export default BotMessage
