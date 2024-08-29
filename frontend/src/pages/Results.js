import React from 'react';
import { useLocation } from 'react-router-dom';

function Results() {
  const location = useLocation();
  const { transcription, summary, handbook } = location.state.data;

  return (
    <div className="results">
      <h2>Results</h2>
      <section>
        <h3>Transcription</h3>
        <p>{transcription}</p>
      </section>
      <section>
        <h3>Summary</h3>
        <p>{summary}</p>
      </section>
      <section>
        <h3>Handbook</h3>
        <p>{handbook}</p>
      </section>
    </div>
  );
}

export default Results;