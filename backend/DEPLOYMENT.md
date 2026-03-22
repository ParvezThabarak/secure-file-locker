# Deployment Guide

This guide covers different deployment options for the S3 File Manager Frontend.

## 🚀 Vercel Deployment (Recommended)

### Prerequisites
- Vercel account
- GitHub repository with the frontend code
- Backend API deployed and accessible

### Steps

1. **Connect Repository**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Build Settings**
   - Framework Preset: `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

3. **Set Environment Variables**
   ```
   VITE_API_URL=https://your-backend-domain.com
   ```

4. **Deploy**
   - Click "Deploy"
   - Vercel will automatically build and deploy your app

### Custom Domain (Optional)
- Go to Project Settings → Domains
- Add your custom domain
- Configure DNS records as instructed

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build the Docker image
docker build -t s3-file-manager-frontend .

# Run the container
docker run -p 3000:80 -e BACKEND_URL=http://your-backend:5000 s3-file-manager-frontend
```

### Docker Compose

```bash
# Create .env file
echo "BACKEND_URL=http://your-backend:5000" > .env

# Start with docker-compose
docker-compose up -d
```

### Production Docker Deployment

1. **Build for production**
   ```bash
   docker build -t s3-file-manager-frontend:latest .
   ```

2. **Push to registry**
   ```bash
   docker tag s3-file-manager-frontend:latest your-registry/s3-file-manager-frontend:latest
   docker push your-registry/s3-file-manager-frontend:latest
   ```

3. **Deploy to cloud provider**
   - AWS ECS, Google Cloud Run, Azure Container Instances
   - Set environment variables for backend URL

## 🌐 Netlify Deployment

### Prerequisites
- Netlify account
- GitHub repository

### Steps

1. **Connect Repository**
   - Go to [Netlify Dashboard](https://app.netlify.com)
   - Click "New site from Git"
   - Connect your GitHub repository

2. **Configure Build Settings**
   - Build Command: `npm run build`
   - Publish Directory: `dist`

3. **Set Environment Variables**
   - Go to Site Settings → Environment Variables
   - Add `VITE_API_URL` with your backend URL

4. **Deploy**
   - Netlify will automatically deploy on every push

## ☁️ AWS S3 + CloudFront

### Prerequisites
- AWS account
- AWS CLI configured

### Steps

1. **Build the application**
   ```bash
   npm run build
   ```

2. **Create S3 bucket**
   ```bash
   aws s3 mb s3://your-bucket-name
   ```

3. **Upload files**
   ```bash
   aws s3 sync dist/ s3://your-bucket-name --delete
   ```

4. **Configure S3 for static hosting**
   ```bash
   aws s3 website s3://your-bucket-name --index-document index.html --error-document index.html
   ```

5. **Set bucket policy for public read**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-bucket-name/*"
       }
     ]
   }
   ```

6. **Create CloudFront distribution**
   - Origin: Your S3 bucket
   - Default Root Object: `index.html`
   - Error Pages: 404 → `/index.html` (for SPA routing)

## 🔧 Environment Configuration

### Development
```env
VITE_API_URL=http://localhost:5000
VITE_ENABLE_DEBUG=true
```

### Production
```env
VITE_API_URL=https://api.yourdomain.com
VITE_ENABLE_DEBUG=false
VITE_ENABLE_ANALYTICS=true
```

## 🔒 Security Considerations

### HTTPS
- Always use HTTPS in production
- Configure your backend to only accept HTTPS requests
- Use secure cookies for authentication

### CORS
- Configure your backend CORS settings
- Only allow your frontend domain
- Include credentials in CORS configuration

### Environment Variables
- Never commit `.env` files to version control
- Use platform-specific environment variable management
- Rotate secrets regularly

## 📊 Performance Optimization

### Build Optimization
- Enable gzip compression
- Use CDN for static assets
- Implement proper caching headers

### Runtime Optimization
- Enable service worker for offline support
- Implement lazy loading for routes
- Optimize images and assets

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check `VITE_API_URL` environment variable
   - Verify backend is running and accessible
   - Check CORS configuration

2. **Build Failures**
   - Ensure Node.js version compatibility
   - Clear node_modules and reinstall
   - Check for TypeScript errors

3. **Routing Issues**
   - Configure server to serve `index.html` for all routes
   - Check `vercel.json` or nginx configuration

### Debug Mode
Enable debug mode by setting:
```env
VITE_ENABLE_DEBUG=true
```

This will show additional console logs and error details.

## 📈 Monitoring

### Analytics
- Google Analytics
- Vercel Analytics
- Custom error tracking

### Performance Monitoring
- Web Vitals
- Lighthouse CI
- Real User Monitoring (RUM)

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```
