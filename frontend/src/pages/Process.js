import React, { useState } from 'react';
import axios from 'axios';
import { useHistory } from 'react-router-dom';

function Process() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [type, setType] = useState('file');
  const history = useHistory();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUrlChange = (e) => {
    setUrl(e.target.value);
  };

  const handleTypeChange = (e) => {
    setType(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    if (type === 'file') {
      formData.append('file', file);
    } else {
      formData.append('url', url);
    }
    formData.append('type', type);

    try {
      const response = await axios.post('/api/process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      history.push('/results', { data: response.data });
    } catch (error) {
      console.error('Error processing file:', error);
    }
  };

  return (
    <div className="process">
      <h2>Process Your File</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>
            <input
              type="radio"
              value="file"
              checked={type === 'file'}
              onChange={handleTypeChange}
            />
            Upload File
          </label>
          <label>
            <input
              type="radio"
              value="youtube"
              checked={type === 'youtube'}
              onChange={handleTypeChange}
            />
            YouTube URL
          </label>
        </div>
        {type === 'file' ? (
          <input type="file" onChange={handleFileChange} />
        ) : (
          <input
            type="text"
            value={url}
            onChange={handleUrlChange}
            placeholder="Enter YouTube URL"
          />
        )}
        <button type="submit">Process</button>
      </form>
    </div>
  );
}

export default Process;