import { Msg } from '../../../../Interfaces/Msg'
import './style.scss'

interface Props{
  msg: Msg
}

function MsgInfo({msg}: Props) {
  return (
    <span className='MsgInfo'>
      <div className="text">
        {msg.msg.split(/\b(https?:\/\/\S+)/gi).map((part, index) => {
          if (part.match(/\bhttps?:\/\/\S+/gi)) {
            return (
              <a href={part} key={index} target="_blank" rel="noopener noreferrer">
                {part}
              </a>
            );
          }
          console.log(part)
          return part;
        })}
      </div>  
      <div className='status'>
        <div className="time">
          {msg.time}
        </div>
        <div className='statusImg'>
          <img src={ msg.status === "sent" ? "../../../public/ic_sent.svg" : "../../../public/ic_read.svg"} alt="" />
        </div>
      </div>
    </span>
  )
}

export default MsgInfo
