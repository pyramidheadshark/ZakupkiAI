import { useDispatch } from 'react-redux'
import './style.scss'
import { setMsgs } from '../../../store/redusers/chatSlice'

interface Props {
  children: string
}

function Link({children}: Props) {

  const dispatch = useDispatch()
  
  async function sendMessage() {
    const date = new Date(Date.now())
    const time = date.getHours() + ":" + date.getMinutes()

    dispatch(setMsgs({Msg:{who: "me", msg: children, time, status: "sent"}, federalLaw: "44-ФЗ"}))
  }

  return (
    <button className="Link" onClick={sendMessage}>
        {children}
    </button>
  )
}

export default Link