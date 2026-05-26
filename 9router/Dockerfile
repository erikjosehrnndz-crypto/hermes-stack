FROM node:20-alpine
RUN npm install -g 9router
ENV NODE_ENV=production PORT=20128 HOSTNAME=0.0.0.0
EXPOSE 20128
CMD ["node", "/usr/local/lib/node_modules/9router/app/server.js"]
