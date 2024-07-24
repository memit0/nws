import logo from './logo.svg';
import './App.css';
import React, {useState, useEffect} from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";

function App() {

  const [articles, setArticles] = useState([]);
  const [weather, setWeather] = useState([
    {
      city_name: 'City',
      temp: 0,
      weather_description: 'Description'
    }
  ]);

  useEffect(() => {
    fetch('/')
      .then(response => response.json())
      .then(data => {
        setArticles(data.articles);
        setWeather(data.weather);
      });
  }, []);

  return (

    <div className="App">
      <div class="weather">
        <div><strong>Weather in {{ weather.city_name }}</strong></div>
        <div class="temp">Temperature: {{ weather.temp }}°C</div>
        <div>Description: {{ weather.weather_description }}</div>
      </div>
      



      {/* <div className="container">
        <h1 className="page-header"> News Weather Site</h1>
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </div> */}
    </div>
    
  );
}

export default App;
