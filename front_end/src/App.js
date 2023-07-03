import axios from "../src/components/server";
import { useEffect, useState } from "react";
function App() {
  const [message, setMessage] = useState("");
  useEffect(() => {
    axios.get("/hello_world").then((response) => {
      console.log(setMessage(response.data.message));
    });
  });
  if (!message) {
    return <p> No message</p>;
  }
  return <div className="App">{message}</div>;
}

export default App;
