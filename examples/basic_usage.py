from promptcue import PromptCueAnalyzer, PromptCueConfig

QUERY = 'Compare Aurora and OpenSearch for RAG on AWS'           # comparison
# QUERY = 'What is the default retention period for CloudWatch Logs?'  # lookup
# QUERY = 'Our Lambda function keeps timing out — how do I fix it?'    # troubleshooting
# QUERY = 'Give me a broad overview of AWS networking services'         # coverage
# QUERY = 'Should we use DynamoDB or RDS for a high-read catalog?'     # recommendation
# QUERY = 'How do I set up a VPC with private subnets?'                # procedure
# QUERY = 'What is new in the latest AWS Lambda runtime?'              # update
# QUERY = 'Evaluate this architecture for a multi-region deployment'   # analysis
# QUERY = 'Hello, how are you?'                                         # chitchat

if __name__ == '__main__':
    analyzer = PromptCueAnalyzer(PromptCueConfig(
        enable_linguistic_extraction = True,
        enable_keyword_extraction    = True,
    ))
    result = analyzer.analyze(QUERY)
    print(result.model_dump_json(indent=2))
