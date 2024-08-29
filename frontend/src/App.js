import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import Process from './pages/Process';
import Results from './pages/Results';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <Switch>
          <Route exact path="/" component={Home} />
          <Route path="/process" component={Process} />
          <Route path="/results" component={Results} />
        </Switch>
        <Footer />
      </div>
    </Router>
  );
}

export default App;