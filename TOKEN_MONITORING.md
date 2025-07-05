# Token Monitoring Integration

This document describes how token monitoring has been integrated into the MedDigest research digest system to prevent rate limit errors and track API usage.

## Overview

The token monitoring system has been integrated into the research digest to:
- Track token usage across all LLM API calls
- Automatically enforce rate limits to prevent API errors
- Provide cost tracking and usage statistics
- Ensure smooth operation without manual rate limiting

## Integration Points

### 1. PaperAnalyzer Class
- **File**: `AI_Processing/paper_analyzer.py`
- **Changes**: 
  - Added `TokenMonitor` import
  - Modified constructor to accept optional `token_monitor` parameter
  - Updated `analyze_paper()` method to track token usage
  - Automatic rate limiting during paper analysis

### 2. ResearchDigest Class
- **File**: `AI_Processing/research_digest.py`
- **Changes**:
  - Added `TokenMonitor` import
  - Created shared token monitor instance
  - Added `_make_llm_call_with_monitoring()` helper method
  - Updated all LLM call methods to use token monitoring
  - Removed manual rate limiting code

### 3. Main Application
- **File**: `main.py`
- **Changes**:
  - Added token usage summary printing after digest generation

## Key Features

### Automatic Rate Limiting
- The token monitor automatically tracks tokens per minute
- When the limit is reached, it automatically sleeps until the next minute
- No manual intervention required

### Token Estimation
- Input tokens: Estimated as `len(prompt) // 4` (rough approximation)
- Output tokens: Estimated as `len(response) // 4`
- This provides reasonable estimates for rate limiting purposes

### Cost Tracking
- Tracks costs for both input and output tokens
- Uses current Groq pricing (input: $0.05/million, output: $0.08/million)
- Provides cost summaries after processing

### Usage Statistics
- Total calls made
- Total tokens used (input + output)
- Total cost incurred
- Per-call breakdown

## Configuration

### Token Limits
The default token limit is set to 16,000 tokens per minute, which is conservative for most API providers. You can adjust this in:

```python
# In ResearchDigest.__init__()
self.token_monitor = TokenMonitor(max_tokens_per_minute=16000)
```

### Cost Rates
Current cost rates are configured in the TokenMonitor class:
```python
INPUT_COST_PER_MILLION = 0.05   # $0.05 per million input tokens
OUTPUT_COST_PER_MILLION = 0.08  # $0.08 per million output tokens
```

## Usage Example

The token monitoring is now automatically active when you run the research digest:

```python
# Initialize research digest (token monitoring is automatic)
digest = ResearchDigest(api_key)

# Generate digest (all calls are automatically rate-limited)
digest_json = digest.generate_digest()

# Print usage summary
digest.token_monitor.print_usage_summary()
```

## Testing

A test script is provided to verify the integration:

```bash
python test_token_monitoring.py
```

This script tests:
- Basic token monitor functionality
- Paper analyzer with token monitoring
- Rate limiting behavior
- Cost calculation

## Benefits

1. **No More Rate Limit Errors**: Automatic rate limiting prevents API errors
2. **Cost Transparency**: Track exactly how much each digest costs
3. **Better Performance**: No manual sleep delays, only when necessary
4. **Usage Insights**: Understand token usage patterns
5. **Reliability**: Consistent operation regardless of API load

## Monitoring Output

After running the digest, you'll see output like:

```
============================================================
TOKEN USAGE SUMMARY
============================================================
Total calls: 45
Total tokens: 125,430
  - Input: 89,200
  - Output: 36,230
Total cost: $0.0089
============================================================
```

## Troubleshooting

### High Token Usage
If you're hitting rate limits frequently:
1. Increase `max_tokens_per_minute` in the TokenMonitor initialization
2. Reduce batch sizes in the research digest
3. Optimize prompts to use fewer tokens

### Cost Concerns
If costs are higher than expected:
1. Review the cost rates in TokenMonitor
2. Check if prompts are unnecessarily long
3. Consider using more efficient models

### Performance Issues
If processing is too slow:
1. Increase the token limit (if your API allows)
2. Reduce the number of papers processed
3. Optimize prompt lengths

## Future Enhancements

Potential improvements to consider:
1. More accurate token counting using tiktoken
2. Dynamic rate limiting based on API response headers
3. Cost alerts when thresholds are exceeded
4. Usage analytics and reporting
5. Integration with multiple API providers 