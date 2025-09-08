import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ArticleList = () => {
    const [articles, setArticles] = useState([]);

    useEffect(() => {
        axios.get(`${API_BASE_URL}/articles`)
            .then(response => {
                setArticles(response.data);
            })
            .catch(error => {
                console.error('Error fetching articles:', error);
            });
    }, []);

    return (
        <div>
            <h1>Articles</h1>
            {articles.map(article => (
                <div key={article.id}>
                    <h2><a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a></h2>
                    <p>{article.summary}</p>
                    <p><strong>Category:</strong> {article.category}</p>
                    <p><strong>Source:</strong> {article.source_name}</p>
                </div>
            ))}
        </div>
    );
};

export default ArticleList;
