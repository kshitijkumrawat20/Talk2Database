# SQL Agent with LangChain and FastAPI

A powerful SQL agent built with LangChain and FastAPI that supports multiple database types (SQLite, PostgreSQL, MySQL) and provides a RESTful API for natural language database queries.

## Project Overview

This project implements an AI-powered SQL agent with a FastAPI backend that can:
- Connect to multiple types of databases (SQLite, PostgreSQL, MySQL)
- Execute SQL queries using natural language prompts
- Provide detailed schema information
- Handle error cases gracefully
- Support secure database connections

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd AiAgents
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   - Copy the `.env.example` file to `.env`
   - Update the environment variables with your configurations:
   ```env
   GROQ_API_KEY=your_groq_api_key
   DB_TYPE=sqlite  # or postgresql, mysql
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USERNAME=your_username
   DB_PASSWORD=your_password
   ```

## Database Configuration

### SQLite (Default)
- No additional configuration needed
- Database will be created as `data.db` in the project directory

### PostgreSQL
1. Create a PostgreSQL database instance
2. Set the following environment variables:
   ```env
   DB_TYPE=postgresql
   POSTGRES_URL=postgresql://username:password@host:port/database
   ```

### MySQL
1. Create a MySQL database instance
2. Set the following environment variables:
   ```env
   DB_TYPE=mysql
   MYSQL_URL=mysql://username:password@host:port/database
   ```

## Running the Application

1. **Start the FastAPI Server**
   ```bash
   uvicorn main:app --reload
   ```

2. **API Endpoints**

   ### Connect to Database
   ```http
   POST /connect
   Content-Type: application/json

   {
     "db_type": "postgresql",
     "connection_string": "postgresql://username:password@host:port/database"
   }
   ```

   ### Execute Query
   ```http
   POST /query
   Content-Type: application/json

   {
     "query": "What is the average salary of employees?"
   }
   ```

   ### Get Schema Information
   ```http
   GET /schema
   ```

3. **Example API Usage with curl**
   ```bash
   # Connect to database
   curl -X POST http://localhost:8000/connect \
     -H "Content-Type: application/json" \
     -d '{"db_type": "postgresql", "connection_string": "postgresql://user:pass@localhost:5432/db"}'

   # Execute query
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the average salary of employees?"}'

   # Get schema
   curl http://localhost:8000/schema
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify database credentials in connection string
   - Check if database server is running
   - Ensure network connectivity and firewall settings
   - Verify the FastAPI server is running

2. **API Errors**
   - Check if FastAPI server is running
   - Verify correct endpoint URLs
   - Ensure proper JSON request format
   - Check API response status codes

3. **Missing Dependencies**
   - Run `pip install -r requirements.txt`
   - Ensure Python version compatibility (Python 3.9+ required)
   - Install database-specific drivers (psycopg2 for PostgreSQL, etc.)

4. **SSL Issues with Cloud Databases**
   - Verify SSL certificates are properly configured
   - Check if SSL is required by your cloud provider
   - Add SSL parameters to connection string if needed

### Error Messages

- `"Error: Query failed"`: Verify SQL syntax and table existence
- `"Connection refused"`: Check database server status and credentials
- `"SSL required"`: Enable SSL in connection string

## Security Considerations

1. **Environment Variables**
   - Never commit `.env` file to version control
   - Use strong passwords for database connections
   - Rotate API keys and credentials regularly

2. **Database Access**
   - Use least privilege principle for database users
   - Enable SSL for cloud database connections
   - Regularly audit database access logs

3. **Code Security**
   - Validate all user inputs
   - Use parameterized queries to prevent SQL injection
   - Keep dependencies updated

## Deployment to AWS EC2

This section covers deploying the backend to AWS EC2 using GitHub Actions and Docker.

### Prerequisites

1. **AWS Resources**
   - An AWS account with appropriate permissions
   - An EC2 instance running (t2.micro or larger) with Docker installed
   - An Elastic Container Registry (ECR) repository
   - Security Group configured to allow inbound traffic on port 80

2. **GitHub Repository Setup**
   - Access to repository settings to configure secrets
   - Main branch protection rules (optional)

### Environment Setup

1. **Required GitHub Secrets**
   Configure the following secrets in your GitHub repository settings:
   ```
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_DEFAULT_REGION=your-aws-region
   ECR_REGISTRY=your-account-id.dkr.ecr.region.amazonaws.com
   ECR_REPOSITORY=your-repository-name
   EC2_HOST=your-ec2-public-dns
   EC2_USER=ec2-user
   EC2_SSH_KEY=your-private-ssh-key
   ```

2. **EC2 Instance Setup**
   ```bash
   # Install Docker
   sudo yum update -y
   sudo yum install docker -y
   sudo service docker start
   sudo usermod -a -G docker ec2-user

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

### Deployment Process

The deployment process is automated through GitHub Actions and includes:

1. **Continuous Integration**
   - Triggered on push to main branch
   - Builds Docker image
   - Runs tests (if configured)
   - Pushes to AWS ECR

2. **Continuous Deployment**
   - Pulls latest image on EC2
   - Updates docker-compose.yml
   - Restarts containers with new version

### Frontend Integration

1. **Update Frontend Configuration**
   Update the API URL in frontend's axiosConfig.js to point to your EC2 instance:
   ```javascript
   const defaultBaseURL = window.location.hostname === 'localhost' 
       ? 'http://localhost:8000/api/v1' 
       : 'http://your-ec2-public-dns/api/v1';
   ```

2. **CORS Configuration**
   Ensure your backend's CORS settings allow requests from your Vercel domain:
   ```python
   # In backend/app/main.py
   origins = [
       "http://localhost:3000",
       "https://your-vercel-domain.vercel.app"
   ]
   ```

### Troubleshooting Deployment

1. **Common Deployment Issues**
   - **GitHub Actions Failures**
     - Verify AWS credentials are correct
     - Check ECR repository permissions
     - Ensure EC2 instance has sufficient disk space

   - **Container Issues**
     - Check Docker logs: `docker logs container_id`
     - Verify environment variables are set correctly
     - Check EC2 instance capacity

2. **Security Best Practices**
   - Regularly rotate AWS access keys
   - Use IAM roles with minimal required permissions
   - Keep EC2 security groups restricted
   - Enable AWS CloudTrail for audit logging
   - Use AWS Secrets Manager for sensitive data

3. **Monitoring**
   - Set up AWS CloudWatch for logs and metrics
   - Configure alerts for instance health
   - Monitor application logs through Docker
   ```bash
   docker-compose logs -f
   ```

## Detailed AWS Setup Guide for Beginners

This section provides a detailed, step-by-step guide for setting up your AWS environment to deploy the backend application using Docker, GitHub Actions, ECR, and EC2.

### Step 1: AWS Account and IAM Setup

1. Sign in to the AWS Management Console.
2. Navigate to the IAM dashboard.
3. Create a new IAM user with programmatic access if needed.
4. Create a new IAM Role for your EC2 instance with the following policies attached:
   - AmazonEC2ContainerRegistryFullAccess
   - AmazonEC2FullAccess
   - AmazonSSMManagedInstanceCore (for Systems Manager access)
   - (Add any additional policies required by your application.)
5. Use this IAM Role for your EC2 instance and ensure the access keys (if using IAM user) are configured in your GitHub Secrets.

### Step 2: Create Your ECR Repository

1. Navigate to the AWS ECR dashboard from the AWS Management Console.
2. Click on 'Create repository' and follow the prompts to create a new Docker repository.
3. Note down the Repository URI; this will be used in GitHub Actions for tagging and pushing your Docker image.

### Step 3: EC2 Instance Setup

1. Launch a new EC2 instance using an Amazon Linux 2 or Ubuntu AMI.
2. During configuration, set up a Security Group that:
   - Allows inbound HTTP traffic on port 80 (or the port used by your backend).
   - Allows inbound SSH traffic on port 22 for administering the server.
3. Once the instance is running, connect to it via SSH.
4. Install Docker:
   - For Amazon Linux 2: run `sudo yum update -y` followed by `sudo yum install docker -y` and start the Docker service with `sudo service docker start`.
   - For Ubuntu: run `sudo apt-get update` followed by `sudo apt-get install docker.io -y` and start Docker with `sudo systemctl start docker`.
5. Install Docker Compose using the official installation instructions:
   - Download it from GitHub (e.g., using curl) and set the executable permissions.

### Step 4: Configuring the EC2 Instance for Deployment

1. Ensure the EC2 instance has the correct IAM Role attached to allow access to ECR and other necessary AWS services.
2. Set up environment variables on your EC2 instance if needed, or include them in your docker-compose configuration.
3. Use SSH to deploy updates via GitHub Actions as specified in your workflow.

### Step 5: Security and Monitoring Best Practices

1. Configure AWS CloudWatch to capture logs and monitor the health of your EC2 instance.
2. Enable AWS CloudTrail for audit logging and enhanced security monitoring.
3. Regularly review and update Security Group rules and IAM policies to adhere to the principle of least privilege.
4. Consider using AWS Secrets Manager for storing sensitive configuration data.

### Connecting Backend and Frontend

- Update the API endpoint in the frontend configuration (for example in `axiosConfig.js`) to point to the EC2 instance's public DNS/IP.
- Make sure that the CORS settings in your backend allow requests from the Vercel domain where the frontend is deployed.
- Test connectivity by accessing the backend API from the frontend once deployment is complete.

## Frontend Integration with Streamlit

The application now includes a Streamlit-based frontend that runs alongside the FastAPI backend in a single container. This section details the frontend structure and setup.

### Frontend Components

1. **Login/Signup Page**
   - User authentication with SQLite database
   - Session management for logged-in users
   - Password hashing and security features

2. **Database Connection Page**
   - Interface to configure database connections
   - Support for SQLite, PostgreSQL, and MySQL
   - Connection testing and validation

3. **Chat Interface**
   - Natural language query input
   - SQL query display and results visualization
   - Query history tracking

### Container Architecture

The application runs both services in a single container:
- FastAPI Backend: Port 8000
- Streamlit Frontend: Port 80

Services are launched using a `start.sh` script that manages both processes:
```bash
# Example start.sh
#!/bin/bash
uvicorn main:app --host 0.0.0.0 --port 8000 &
streamlit run frontend/app.py --server.port 80 --server.address 0.0.0.0
```

### Building and Running

1. **Build the Container**
   ```bash
   docker-compose build
   ```

2. **Start the Services**
   ```bash
   docker-compose up
   ```

3. **Access the Application**
   - Frontend: http://localhost (Port 80)
   - Backend API: http://localhost:8000/api/v1

### API Integration

The frontend communicates with the backend using the following base URL:
```python
API_BASE_URL = "http://localhost:8000/api/v1"
```

Key API endpoints used by the frontend:
- POST /api/v1/auth/login
- POST /api/v1/auth/signup
- POST /api/v1/connect
- POST /api/v1/query
- GET /api/v1/schema

### Troubleshooting

1. **Process Management Issues**
   - Check container logs: `docker-compose logs`
   - Verify both services are running: `docker-compose ps`
   - Restart container if services fail: `docker-compose restart`

2. **Port Conflicts**
   - Ensure ports 80 and 8000 are available
   - Modify port mappings in docker-compose.yml if needed
   - Check for other services using these ports

3. **Frontend-Backend Communication**
   - Verify API base URL configuration
   - Check CORS settings in FastAPI
   - Ensure network connectivity between services

4. **Authentication Issues**
   - Verify SQLite database permissions
   - Check session management configuration
   - Clear browser cache and cookies if needed

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
