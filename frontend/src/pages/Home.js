import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div className="home">
      <h1>Welcome to Note Crew</h1>
      <p>Create handbooks from various sources including audio, images, YouTube videos, and text.</p>
      <Link to="/process" className="cta-button">Get Started</Link>
    </div>
  );
}

export default Home;