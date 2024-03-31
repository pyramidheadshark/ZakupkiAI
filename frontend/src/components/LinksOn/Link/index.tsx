import { useDispatch } from 'react-redux'
import './style.scss'
import { fetchPush, setMsgs } from '../../../store/redusers/chatSlice'
import { AppDispatch } from '../../../store'

interface Props {
  children: string
}

function Link({children}: Props) {

  const dispatch = useDispatch<AppDispatch>()
  
  async function sendMessage() {
    dispatch(fetchPush({text: children, federalLaw: "44-ФЗ"}));
  }

  return (
    <button className="Link" onClick={sendMessage}>
        {children}
    </button>
  )
}

export default Link