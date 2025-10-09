package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"
	_ "github.com/lib/pq"
)

type Record struct {
	ID     int    `json:"id"`
	Number int    `json:"number"`
	Date   string `json:"date"`
}

func formatJSON(v interface{}) ([]byte, error) {
	buf := new(bytes.Buffer)
	enc := json.NewEncoder(buf)
	enc.SetIndent("", "")
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	result := buf.Bytes()
	result = bytes.ReplaceAll(result, []byte(`":`), []byte(`": `))
	result = bytes.ReplaceAll(result, []byte(`,"`), []byte(`, "`))
	return bytes.TrimSpace(result), nil
}

var db *sql.DB

func main() {
	var err error
	connStr := "host=" + getEnv("POSTGRES_HOST", "db") +
		" port=" + getEnv("POSTGRES_PORT", "5432") +
		" user=" + getEnv("POSTGRES_USER", "postgres") +
		" password=" + getEnv("POSTGRES_PASSWORD", "postgres") +
		" dbname=" + getEnv("POSTGRES_DB", "appdb") +
		" sslmode=disable"

	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	for i := 0; i < 30; i++ {
		err = db.Ping()
		if err == nil {
			break
		}
		time.Sleep(1 * time.Second)
	}

	if err != nil {
		log.Fatal(err)
	}

	http.HandleFunc("/save", saveHandler)
	http.HandleFunc("/read", readHandler)
	http.HandleFunc("/getlast", getLastHandler)

	log.Println("Go app listening on :8001")
	log.Fatal(http.ListenAndServe(":8001", nil))
}

func saveHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid method", http.StatusBadRequest)
		return
	}

	var data struct {
		Number int    `json:"number"`
		Date   string `json:"date"`
	}

	if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	var id int
	err := db.QueryRow(
		"INSERT INTO go_schema.records (number, date) VALUES ($1, $2) RETURNING id",
		data.Number, data.Date,
	).Scan(&id)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	response := Record{
		ID:     id,
		Number: data.Number,
		Date:   data.Date,
	}

	w.Header().Set("Content-Type", "application/json")
	jsonData, _ := formatJSON(response)
	w.Write(jsonData)
}

func readHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Invalid method", http.StatusBadRequest)
		return
	}

	rows, err := db.Query("SELECT id, number, date FROM go_schema.records")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var records []Record
	for rows.Next() {
		var r Record
		var dateTime time.Time
		if err := rows.Scan(&r.ID, &r.Number, &dateTime); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		r.Date = dateTime.Format("2006-01-02")
		records = append(records, r)
	}

	response := map[string][]Record{"records": records}
	w.Header().Set("Content-Type", "application/json")
	jsonData, _ := formatJSON(response)
	w.Write(jsonData)
}

func getLastHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Invalid method", http.StatusBadRequest)
		return
	}

	var record Record
	var dateTime time.Time
	err := db.QueryRow("SELECT id, number, date FROM go_schema.records ORDER BY id DESC LIMIT 1").Scan(&record.ID, &record.Number, &dateTime)
	if err != nil {
		if err == sql.ErrNoRows {
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte("{}"))
			return
		}
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	record.Date = dateTime.Format("2006-01-02")
	w.Header().Set("Content-Type", "application/json")
	jsonData, _ := formatJSON(record)
	w.Write(jsonData)
}

func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
