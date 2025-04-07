# Moskal Report Generator

A comprehensive social media monitoring and report generation system that analyzes social media presence, sentiment, and generates detailed reports.

## Features

- **Social Media Monitoring**
  - Track mentions across multiple platforms
  - Analyze sentiment trends
  - Monitor key opinion leaders (KOL)
  - Calculate presence scores

- **Report Generation**
  - Automated PowerPoint report creation
  - PDF conversion capabilities
  - Customizable report templates
  - Data visualization with charts and graphs

- **Analytics**
  - Sentiment analysis
  - Topic overview and trending topics
  - Reach and engagement metrics
  - Context-based analysis

## Project Structure

```
.
├── chart_generator/       # Chart generation modules
│   ├── context.py        # Context analysis
│   ├── kol.py           # Key Opinion Leaders analysis
│   ├── mentions.py      # Mentions tracking
│   ├── metrics.py       # Metrics calculation
│   ├── sentiment.py     # Sentiment analysis
│   └── topics.py        # Topic analysis
│
├── report_generator/     # Report generation modules
│   ├── functions.py     # Helper functions
│   └── slider.py        # PowerPoint slide generation
│
├── utils/               # Utility modules
│   ├── functions.py     # Common utilities
│   ├── gemini.py       # Gemini AI integration
│   └── send_email.py   # Email functionality
│
├── main.py             # Main application entry point
├── ppt_generator.py    # PowerPoint generation
├── pdf_convert.py      # PDF conversion
└── requirements.txt    # Project dependencies
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/mocharil/moskal-report.git
cd moskal-report
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Docker Setup

1. Build the Docker image:
```bash
docker build -t moskal-report .
```

2. Run the container:
```bash
docker run -p 8000:8000 moskal-report
```

## Usage

1. Configure monitoring parameters in `.env`
2. Run the main application:
```bash
python main.py
```

3. Access the monitoring dashboard at `http://localhost:8000`

## Environment Variables

Required environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud credentials
- `EMAIL_SENDER`: Email sender address
- `EMAIL_PASSWORD`: Email sender password
- `GEMINI_API_KEY`: Google Gemini API key

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
