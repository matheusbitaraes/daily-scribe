"""
Article Summarization Service for Daily Scribe application.

This module handles summarizing article content using AI models.
Currently implements a mock summarization that returns the first paragraph
until a real LLM integration is ready.
"""

import logging
import time
from typing import Optional, Dict, Any
class SummarizationResult:
    """Result of article summarization."""
    
    def __init__(self, summary, processing_time, word_count, success, error_message=None):
        self.summary = summary
        self.processing_time = processing_time
        self.word_count = word_count
        self.success = success
        self.error_message = error_message


class SummarizationError(Exception):
    """Custom exception for summarization errors."""
    pass


class ArticleSummarizer:
    """Handles article summarization using AI models."""
    
    def __init__(self, 
                 max_input_length: int = 3000,
                 target_summary_length: int = 300,
                 min_summary_length: int = 50):
        """
        Initialize the article summarizer.
        
        Args:
            max_input_length: Maximum input text length in words
            target_summary_length: Target summary length in characters
            min_summary_length: Minimum summary length in characters
        """
        self.max_input_length = max_input_length
        self.target_summary_length = target_summary_length
        self.min_summary_length = min_summary_length
        self.logger = logging.getLogger(__name__)
        
        # Model configuration (for future LLM integration)
        self.model_config = {
            'model_name': 'mock-summarizer-v1',
            'temperature': 0.7,
            'max_tokens': 150,
            'strategy': 'first_paragraph_mock'
        }
    
    def summarize_article(self, content: str, first_paragraph: Optional[str] = None) -> SummarizationResult:
        """
        Summarize an article's content.
        
        Args:
            content: Full article content
            first_paragraph: Optional first paragraph (for mock implementation)
            
        Returns:
            SummarizationResult with summary and metadata
        """
        start_time = time.time()
        self.logger.debug(f"Starting summarization of {len(content)} character article")
        
        try:
            # Validate input
            if not content or not content.strip():
                return SummarizationResult(
                    summary="",
                    processing_time=0.0,
                    word_count=0,
                    success=False,
                    error_message="Empty content provided"
                )
            
            # Preprocess content
            processed_content = self._preprocess_content(content)
            word_count = len(processed_content.split())
            
            # Check content length
            if word_count > self.max_input_length:
                self.logger.warning(f"Content too long ({word_count} words), truncating to {self.max_input_length}")
                words = processed_content.split()[:self.max_input_length]
                processed_content = ' '.join(words)
                word_count = self.max_input_length
            
            # Generate summary using mock implementation
            summary = self._generate_mock_summary(processed_content, first_paragraph)
            
            processing_time = time.time() - start_time
            
            # Validate summary
            if len(summary) < self.min_summary_length:
                self.logger.warning(f"Summary too short ({len(summary)} chars), using fallback")
                summary = self._generate_fallback_summary(processed_content)
            
            self.logger.info(f"Summarization completed in {processing_time:.2f}s: {len(summary)} chars")
            
            return SummarizationResult(
                summary=summary,
                processing_time=processing_time,
                word_count=word_count,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Summarization failed: {str(e)}"
            self.logger.error(error_msg)
            
            return SummarizationResult(
                summary="",
                processing_time=processing_time,
                word_count=0,
                success=False,
                error_message=error_msg
            )
    
    def _preprocess_content(self, content: str) -> str:
        """
        Preprocess content before summarization.
        
        Args:
            content: Raw article content
            
        Returns:
            Preprocessed content
        """
        # Remove extra whitespace
        import re
        content = re.sub(r'\s+', ' ', content)
        
        # Remove very short lines that are likely not content
        lines = content.split('\n')
        substantial_lines = [line.strip() for line in lines if len(line.strip()) > 20]
        
        return '\n'.join(substantial_lines).strip()
    
    def _generate_mock_summary(self, content: str, first_paragraph: Optional[str] = None) -> str:
        """
        Generate a mock summary using the first paragraph strategy.
        
        This is a placeholder implementation that will be replaced with
        actual LLM-based summarization.
        
        Args:
            content: Full article content
            first_paragraph: Pre-extracted first paragraph
            
        Returns:
            Mock summary based on first paragraph
        """
        self.logger.debug("Using mock summarization strategy: first_paragraph")
        
        # Use provided first paragraph or extract it
        if first_paragraph and len(first_paragraph.strip()) >= self.min_summary_length:
            summary = first_paragraph.strip()
        else:
            summary = self._extract_first_substantial_paragraph(content)
        
        # Ensure summary meets length requirements
        if len(summary) > self.target_summary_length:
            summary = self._truncate_to_sentence_boundary(summary, self.target_summary_length)
        
        # Add mock LLM indicator
        summary = f"{summary}"
        
        return summary
    
    def _extract_first_substantial_paragraph(self, content: str) -> str:
        """
        Extract the first substantial paragraph from content.
        
        Args:
            content: Article content
            
        Returns:
            First substantial paragraph
        """
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for paragraph in paragraphs:
            # Skip very short paragraphs (likely headers, dates, etc.)
            if len(paragraph) >= self.min_summary_length:
                return paragraph
        
        # Fallback: use first paragraph even if short
        if paragraphs:
            return paragraphs[0]
        
        # Last resort: use beginning of content
        return content[:self.target_summary_length] if content else ""
    
    def _truncate_to_sentence_boundary(self, text: str, max_length: int) -> str:
        """
        Truncate text to a sentence boundary within max_length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text ending at sentence boundary
        """
        if len(text) <= max_length:
            return text
        
        # Find the last sentence boundary within the limit
        truncated = text[:max_length]
        
        # Look for sentence endings
        sentence_endings = ['. ', '! ', '? ']
        last_boundary = -1
        
        for ending in sentence_endings:
            pos = truncated.rfind(ending)
            if pos > last_boundary:
                last_boundary = pos + 1  # Include the punctuation
        
        if last_boundary > 0 and last_boundary > max_length * 0.7:  # Don't cut too much
            return text[:last_boundary].strip()
        else:
            # Fallback: truncate at word boundary
            words = truncated.split()
            return ' '.join(words[:-1]) + '...'
    
    def _generate_fallback_summary(self, content: str) -> str:
        """
        Generate a fallback summary when other methods fail.
        
        Args:
            content: Article content
            
        Returns:
            Fallback summary
        """
        # Simple fallback: first 200 characters at word boundary
        if len(content) <= 200:
            return content
        
        truncated = content[:200]
        words = truncated.split()
        return ' '.join(words[:-1]) + '...'
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Model configuration dictionary
        """
        return {
            **self.model_config,
            'max_input_length': self.max_input_length,
            'target_summary_length': self.target_summary_length,
            'min_summary_length': self.min_summary_length,
            'status': 'mock_implementation'
        }


def summarize_article(content: str, first_paragraph: Optional[str] = None) -> SummarizationResult:
    """
    Convenience function to summarize an article.
    
    Args:
        content: Full article content
        first_paragraph: Optional first paragraph
        
    Returns:
        SummarizationResult
    """
    summarizer = ArticleSummarizer()
    return summarizer.summarize_article(content, first_paragraph)


if __name__ == "__main__":
    # Test the article summarizer
    import logging
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test content
    test_content = """
    Breaking News: Technology Advancement Changes Everything
    
    In a groundbreaking development that could reshape the future of technology, researchers have announced a major breakthrough in artificial intelligence. The new system demonstrates unprecedented capabilities in understanding and processing human language, marking a significant milestone in the field of machine learning.
    
    The research team, led by Dr. Jane Smith at the Institute of Technology, has been working on this project for over three years. Their innovative approach combines advanced neural networks with novel training techniques to achieve results that were previously thought impossible.
    
    "This is a game-changer for the industry," said Dr. Smith during a press conference yesterday. "We've managed to create a system that not only understands context but can also reason about complex problems in ways we've never seen before."
    
    The implications of this breakthrough extend far beyond the laboratory. Industries ranging from healthcare to finance are already exploring how this technology could revolutionize their operations. Early trials have shown promising results in medical diagnosis, financial analysis, and automated customer service.
    
    However, the development also raises important questions about the future of work and the ethical implications of such powerful AI systems. Experts are calling for careful consideration of how this technology should be deployed and regulated.
    
    The research team plans to publish their findings in the upcoming issue of the Journal of Artificial Intelligence. They have also announced plans for a public demonstration of the system next month.
    """
    
    print("Testing Article Summarizer...")
    print(f"Content length: {len(test_content)} characters")
    
    result = summarize_article(test_content)
    
    if result.success:
        print(f"\nSummarization successful!")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Word count: {result.word_count}")
        print(f"Summary length: {len(result.summary)} characters")
        print(f"\nSummary:")
        print(f"{result.summary}")
    else:
        print(f"Summarization failed: {result.error_message}")
    
    # Test model info
    summarizer = ArticleSummarizer()
    model_info = summarizer.get_model_info()
    print(f"\nModel info: {model_info}")