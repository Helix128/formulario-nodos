module.exports = {
  apps: [
    {
      name: "formulario-nodos",
      script: "./.venv/bin/gunicorn",
      args: "app.main:app -k uvicorn.workers.UvicornWorker --workers 2 --bind 127.0.0.1:8104",
      cwd: __dirname,
      interpreter: "none",
      env: { PYTHONUNBUFFERED: "1" },
    },
  ],
};
