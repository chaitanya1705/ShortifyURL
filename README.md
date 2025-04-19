# ShortifyURL-Load-Balanced URL Shortener

## Project Overview
This project is a containerized URL shortener service that allows users to submit long URLs and get a shortened version. The system is designed to be scalable using Docker and Kubernetes, with a load balancer distributing requests across multiple instances. The URL mappings are stored in an in-memory key-value store (Redis).

## Technologies Used
- **Docker** for containerization
- **Kubernetes** for orchestration
- **Redis** for in-memory data storage
- **Horizontal Pod Autoscaler (HPA)** for auto-scaling
- **Ingress/LoadBalancer** for traffic routing
- **CI/CD (optional)** for automation

## Project Structure
url-shortener/
├── app.py                    # Main URL shortener application
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container definition
├── docker-compose.yml        # Local development setup
├── templates/
│   └── index.html            # Web frontend
├── kubernetes/
│   ├── namespace.yaml        # Kubernetes namespace
│   ├── configmap.yaml        # Environment variables
│   ├── secret.yaml           # Sensitive information
│   ├── redis.yaml            # Redis deployment and service
│   ├── url-shortener.yaml    # Main app deployment and service
│   ├── hpa.yaml              # Horizontal Pod Autoscaler
│   └── ingress.yaml          # Ingress configuration
├── tests/
│   ├── __init__.py
│   └── test_app.py           # Unit tests for the application
├── scripts/
│   └── stress_test.py        # Load testing script
├── postgres/                 # Optional PostgreSQL integration
│   ├── app_postgres.py       # PostgreSQL version of the app
│   └── requirements_postgres.txt
└── .github/
    └── workflows/
        └── ci-cd.yml         # GitHub Actions workflow


---

## Setup and Deployment

### Week 1: Docker Setup
#### Build and Run with Docker Compose
sh
docker-compose up --build

#### Manually Build and Run Containers
sh
docker build -t url-shortener .
docker run -d --name redis redis:alpine
docker run -d --name url-shortener -p 5000:5000 --link redis:redis -e REDIS_HOST=redis url-shortener

#### Test the API
sh
$body = @{
    url = "<Any-url>"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/shorten" -Method Post -ContentType "application/json" -Body $body

#### Get Stats
sh
Invoke-RestMethod -Uri "http://localhost:5000/stats" -Method Get

Close all other terminals and run 
sh
docker-compose down

---

### Week 2: Kubernetes Deployment
#### Build and Tag Docker Image
sh
docker build -t url-shortener:latest .

#### Load Image into Minikube (if using Minikube)
sh
minikube image load url-shortener:latest

#### Deploy to Kubernetes
sh
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/redis.yaml
kubectl apply -f kubernetes/url-shortener.yaml

#### Check Deployment Status
sh
kubectl get pods -n url-shortener
kubectl get services -n url-shortener

#### Access the Service
If using Minikube:
sh
minikube service url-shortener-service -n url-shortener --url

Test with curl:
sh
export SERVICE_URL=$(minikube service url-shortener-service -n url-shortener --url)
curl -X POST -H "Content-Type: application/json" -d '{"url":"https://example.com/very/long/url"}' $SERVICE_URL/shorten

OR For Powershell
sh
$SERVICE_URL = minikube service url-shortener-service -n url-shortener --url
Invoke-RestMethod -Uri "$SERVICE_URL/shorten" -Method Post -ContentType "application/json" -Body '{"url":"https://example.com/very/long/url"}'

---

### Week 3: Scaling, Load Balancing & Monitoring
#### Apply HPA and Ingress
sh
kubectl apply -f kubernetes/hpa.yaml
kubectl apply -f kubernetes/ingress.yaml

#### Monitor the System
sh
kubectl get hpa -n url-shortener
kubectl get pods -n url-shortener -w

#### In a new terminal
sh
minikube addons enable metrics-server
kubectl top pods -n url-shortener

sh
kubectl logs -l app=url-shortener -n url-shortener --tail=100 -f


#### Run Stress Test
sh
pip install requests
python scripts/stress_test.py --url http:// --requests 1000 --concurrency 50

#### Scale Manually (if needed)
sh
kubectl scale deployment url-shortener -n url-shortener --replicas=5

#### Check Namespace Events
sh
kubectl get events -n url-shortener


---

## Future Enhancements (Optional)
- **Database Integration**: Replace Redis with PostgreSQL, MongoDB, or DynamoDB.
- **CI/CD**: Automate testing and deployment with GitHub Actions or Jenkins.

---

## Contributors
- CHAITANYA N
- CHANNAVEER UPASE
- CHETHAN M
- DARSHAN BM

This project is part of the **Cloud Computing Course (UE22CS351B)**, Semester 6 (2025).
