import json
import os
import pandas as pd
import re
from typing import Dict, List, Any, Union

# Import utilitas dari paket utils (sesuaikan dengan environment Anda)
from chart_generator.functions import call_gemini

def generate_executive_summary(TOPIC, START_DATE, END_DATE, SAVE_PATH):
    """
    Membuat executive summary berdasarkan analisis data dari file JSON dan CSV 
    yang disimpan di SAVE_PATH.
    
    Parameters:
    -----------
    TOPIC : str
        Topik utama yang dianalisis
    START_DATE : str
        Tanggal awal periode analisis
    END_DATE : str
        Tanggal akhir periode analisis
    SAVE_PATH : str
        Path direktori tempat semua file analisis disimpan
        
    Returns:
    --------
    Dict
        Executive summary dalam format JSON
    """
    # Inisialisasi dictionary untuk menyimpan semua data
    data = {}
    
    # 1. Load sentiment_breakdown.json
    try:
        with open(os.path.join(SAVE_PATH, 'sentiment_breakdown.json'), 'r') as f:
            data['sentiment_counts'] = json.load(f)
       
    except Exception as e:
        print(f"Error loading sentiment breakdown: {e}")
        data['sentiment_counts'] = {}
    
    # 2. Load sentiment_by_categories.json
    try:
        with open(os.path.join(SAVE_PATH, 'sentiment_by_categories.json'), 'r') as f:
            data['pivot_sentiment'] = json.load(f)
  
    except Exception as e:
        print(f"Error loading sentiment by categories: {e}")
        data['pivot_sentiment'] = []
    
    # 3. Load presence_score_analysis.json
    try:
        with open(os.path.join(SAVE_PATH, 'presence_score_analysis.json'), 'r') as f:
            data['presence_score_analysis'] = json.load(f)
       
    except Exception as e:
        print(f"Error loading presence score analysis: {e}")
        data['presence_score_analysis'] = {}
    
    # 4. Load sentiment_analysis.json
    try:
        with open(os.path.join(SAVE_PATH, 'sentiment_analysis.json'), 'r') as f:
            data['sentiment_analysis'] = json.load(f)
        
    except Exception as e:
        print(f"Error loading sentiment analysis: {e}")
        data['sentiment_analysis'] = {}
    
    # 5. Load popular_mentions.csv
    try:
        data['popular_mentions'] = pd.read_csv(os.path.join(SAVE_PATH, 'popular_mentions.csv')).to_dict(orient='records')[:5]  # Limit to top 5
  
    except Exception as e:
        print(f"Error loading popular mentions: {e}")
        data['popular_mentions'] = []
    
    # 6. Load KOL data
    try:
        kol_data = []
        with open(os.path.join(SAVE_PATH, 'kol.json'), 'r') as f:
            for line in f:
                kol_data.append(json.loads(line.strip()))
        data['kol_data'] = kol_data[:5]  # Limit to top 5
     
    except Exception as e:
        print(f"Error loading KOL data: {e}")
        data['kol_data'] = []
    
    # 7. Load topic_overview.json
    try:
        topic_data = []
        with open(os.path.join(SAVE_PATH, 'topic_overview.json'), 'r') as f:
            for line in f:
                topic_data.append(json.loads(line.strip()))
        data['top_entities'] = topic_data[:10]  # Limit to top 10
     
    except Exception as e:
        print(f"Error loading topic overview: {e}")
        data['top_entities'] = []
    
    # 8. Try to load recommendations.json if available
    try:
        with open(os.path.join(SAVE_PATH, 'recommendations.json'), 'r') as f:
            data['recommendations'] = json.load(f)
   
    except Exception as e:
        print(f"Error loading recommendations: {e}")
        data['recommendations'] = []
    
    # Extract platform data from sentiment_by_categories.json for list of top platforms
    top_platforms = []
    if data['pivot_sentiment']:
        # Sort by total_mentions and get top 5 platforms
        sorted_platforms = sorted(data['pivot_sentiment'], key=lambda x: x.get('total_mentions', 0), reverse=True)
        top_platforms = [p.get('channel', '') for p in sorted_platforms[:5] if p.get('channel')]
    
    # Calculate basic metrics for the summary
    total_mentions = sum(data['sentiment_counts'].values()) if data['sentiment_counts'] else 0
    
    # Calculate sentiment percentages
    sentiment_percentages = {}
    if total_mentions > 0 and data['sentiment_counts']:
        for sentiment, count in data['sentiment_counts'].items():
            sentiment_percentages[sentiment] = round((count / total_mentions) * 100, 1)
    
    # Build the prompt
    prompt = f"""
    You are a senior data analyst specializing in social media insights. Create a comprehensive executive summary of data about [{TOPIC}] for the period [{START_DATE}] to [{END_DATE}].

    ## SENTIMENT DATA
    
    Overall sentiment distribution:
    {data['sentiment_counts']}
    
    Sentiment percentages:
    {sentiment_percentages}
    
    Sentiment by platform/channel:
    {data['pivot_sentiment'][:5] if data['pivot_sentiment'] else "No data available"}
    """
    
    # Add presence score analysis if available
    if data['presence_score_analysis']:
        prompt += f"""
    ## PRESENCE SCORE ANALYSIS
    
    Overall presence score trends:
    {data['presence_score_analysis']}
    """
    
    # Add sentiment analysis if available
    if data['sentiment_analysis']:
        prompt += f"""
    ## DETAILED SENTIMENT ANALYSIS
    
    In-depth sentiment analysis:
    {data['sentiment_analysis']}
    """
    
    # Add popular mentions if available
    if data['popular_mentions']:
        prompt += f"""
    ## POPULAR MENTIONS
    
    Sample of popular posts:
    {data['popular_mentions'][:3]}
    """
    
    # Add top entities if available
    if data['top_entities']:
        prompt += f"""
    ## TOP ENTITIES/TOPICS
    
    Most discussed entities or subtopics:
    {data['top_entities'][:8]}
    """
    
    # Add KOL data if available
    if data['kol_data']:
        prompt += f"""
    ## KEY OPINION LEADERS
    
    Top influencers discussing this topic:
    {data['kol_data'][:3]}
    """
    
    # Add list of top platforms
    prompt += f"""
    ## TOP PLATFORMS
    
    The most active platforms for this topic are:
    {top_platforms if top_platforms else "Data not available"}
    """
    
    # Add recommendations if available
    if data['recommendations']:
        prompt += f"""
    ## STRATEGIC RECOMMENDATIONS
    
    Key recommendations based on the data:
    {data['recommendations']}
    """
    
    # Instruksi dan format output
    prompt += f"""
    ## TASK
    
    Based on all the data above, create a concise executive summary about [{TOPIC}] discussion in social media for the period [{START_DATE}] to [{END_DATE}].

    Format your response as a JSON object with the following structure:
    
    {{
      "summary": {{
        "scope_and_sentiment": {{
          "title": "Scope and Overall Sentiment:",
          "points": [
            "Point about total mentions with specific numbers and dominant sentiment",
            "Point about negative mentions percentage, with context if possible",
            "Point about the nature of coverage (factual, opinion-based, etc.)"
          ]
        }},
        "dominant_topics": {{
          "title": "Dominant Topics:",
          "topics": [
            {{
              "name": "Topic name with highest reach",
              "reach": "Specific reach number in millions if available",
              "sentiment": "Sentiment percentage breakdown",
              "key_points": [
                "Important detail or projection about this topic",
                "Additional context if relevant"
              ]
            }},
            // Include 3-5 more topics with similar structure
          ]
        }},
        "peak_periods": {{
          "title": "Peak Periods:",
          "points": [
            "Specific date range with highest positive coverage with explanation",
            "Specific date range with highest engagement with explanation if different"
          ]
        }},
        "negative_sentiment": {{
          "title": "Negative Sentiment Analysis:",
          "mentions": [
            {{
              "source": "Source of negative mention",
              "description": "Brief description of the criticism"
            }},
            // Include all negative mentions if few, or categorize if many
          ]
        }},
        "key_recommendations": {{
          "title": "Key Recommendations:",
          "points": [
            "Strategic recommendation 1 based on the data",
            "Strategic recommendation 2 based on the data",
            "Strategic recommendation 3 based on the data"
          ]
        }}
      }}
    }}

    The summary should be concise but comprehensive, with specific numbers and percentages where available. Use bullet-point style within the JSON structure for clarity and readability.

    IMPORTANT: Ensure your output is ONLY the properly formatted JSON with no additional text, markdown, or explanatory content.
    """
    
    try:
        # Call LLM to generate executive summary
        summary_text = call_gemini(prompt)
        
        # Try to parse JSON directly
        try:
            summary = json.loads(re.findall(r'\{.*\}',summary_text, flags = re.I|re.S)[0])
        except json.JSONDecodeError:
            # Use regex as fallback if direct parsing fails
            print("Direct JSON parsing failed, trying regex extraction...")
            json_pattern = re.compile(r'\{\s*"title".*\}\s*\}', re.DOTALL)
            json_match = json_pattern.search(summary_text)
            
            if json_match:
                json_str = json_match.group(0)
                summary = json.loads(json_str)
            else:
                # Create fallback summary
                print("JSON extraction failed, creating fallback summary...")
                summary = {
                    "title": f"Executive Summary: {TOPIC} {START_DATE} to {END_DATE}",
                    "summary": {
                        "overview": "Unable to generate comprehensive overview due to parsing issues.",
                        "key_metrics": [
                            {
                                "name": "Total Mentions",
                                "value": total_mentions,
                                "insight": "Data available but parsing failed"
                            }
                        ],
                        "sentiment_analysis": {
                            "overall_sentiment": "Data available but parsing failed",
                            "sentiment_trend": "Data available but parsing failed",
                            "key_sentiment_drivers": [
                                "Data available but parsing failed"
                            ]
                        },
                        "platform_insights": [],
                        "key_topics": [],
                        "influencers": [],
                        "timeline_highlights": [],
                        "recommendations_summary": []
                    }
                }
        
        # Save the executive summary to file
        with open(os.path.join(SAVE_PATH, 'executive_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
            
        return summary
        
    except Exception as e:
        print(summary_text)
        print(f"Error generating executive summary: {e}")
        # Return fallback summary
        fallback_summary = {
            "title": f"Executive Summary: {TOPIC} {START_DATE} to {END_DATE}",
            "summary": {
                "overview": "Unable to generate summary due to an error in processing.",
                "error": str(e)
            },
            "output": str(summary_text)
        }
        
        with open(os.path.join(SAVE_PATH, 'executive_summary_error.json'), 'w') as f:
            json.dump(fallback_summary, f, indent=2)
            
        return fallback_summary
