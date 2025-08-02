FROM golang:1.22-alpine
WORKDIR /app
RUN echo 'package main\n\nimport (\n\t"fmt"\n\t"net/http"\n)\n\nfunc healthHandler(w http.ResponseWriter, r *http.Request) {\n\tw.WriteHeader(http.StatusOK)\n\tfmt.Fprint(w, "ok")\n}\n\nfunc apiHandler(w http.ResponseWriter, r *http.Request) {\n\tfmt.Fprintf(w, "¡Hola desde la API de Go!")\n}\n\nfunc main() {\n\thttp.HandleFunc("/", apiHandler)\n\thttp.HandleFunc("/health", healthHandler)\n\tfmt.Println("Servidor API escuchando en el puerto 8081")\n\thttp.ListenAndServe(":8081", nil)\n}' > main.go
RUN go mod init api
RUN go mod tidy
RUN go build -o /go-api-server .
EXPOSE 8081
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD curl -f http://localhost:8081/health || exit 1
CMD [ "/go-api-server" ]
