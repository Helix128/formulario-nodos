module.exports = {
  apps: [
    {
      name: "formulario-nodos",
      script: "./.venv/bin/gunicorn",
      args: "--bind 0.0.0.0:8104 --workers 4 -k uvicorn.workers.UvicornWorker app.main:app",
      cwd: __dirname,
      interpreter: "none",
      env: { PYTHONUNBUFFERED: "1" },
    },
  ],
};
