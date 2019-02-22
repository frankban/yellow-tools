package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	// procs holds the number of concurrent requests to Github API.
	procs = 5
	// perPage holds the number of repositories returned on a single page by
	// Github (maximum allowed is 100).
	perPage = 100
	// url holds the address of the Github API.
	url = "https://api.github.com/user/repos"
)

func main() {
	cfg, creds := parseArgs()
	done := make(chan struct{})
	pages := make(chan int, procs)
	results := make(chan result)
	// Start producing pages.
	go func() {
		var page int
		for {
			page++
			select {
			case pages <- page:
			case <-done:
				return
			}
		}
	}()
	// Go fetch info about available repositories.
	var wg sync.WaitGroup
	wg.Add(procs)
	for i := 0; i < procs; i++ {
		go func() {
			fetch(pages, results, creds)
			wg.Done()
		}()
	}
	go func() {
		wg.Wait()
		close(results)
		close(done)
	}()
	// Output results.
	for result := range results {
		if result.err != nil {
			fmt.Fprintln(os.Stderr, result.err.Error())
			continue
		}
		for _, repo := range result.repos {
			if !(cfg.excludePersonal && strings.HasPrefix(repo.Name, creds.username+"/")) && repo.matches(cfg.query) {
				repo.print(cfg.verbose)
			}
		}
	}
}

// parseArgs sets and parses command line arguments.
func parseArgs() (config, *credentials) {
	app := filepath.Base(os.Args[0])
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "%s - find your repos on Github\n", app)
		fmt.Fprintf(os.Stderr, "usage: %s [OPTIONS] [query] ...\n", app)
		flag.PrintDefaults()
	}

	// Define flags.
	auth := flag.String("u", "", `colon separated credentials for Github HTTP basic auth
you can use Github username and personal access token generated at
https://github.com/settings/tokens
credentials can be also provided using the GITHUB_AUTH environment variable
`)
	excludePersonal := flag.Bool("o", false, "exclude personal repositories")
	verbose := flag.Bool("v", false, "output additional repository info")

	// Parse flags.
	flag.Parse()
	if *auth == "" {
		*auth = os.Getenv("GITHUB_AUTH")
	}
	userpass := strings.SplitN(*auth, ":", 2)
	if len(userpass) != 2 {
		log.Fatal("cannot find credentials: use either the -u flag or the GITHUB_AUTH env var")
	}
	cfg := config{
		query:           flag.Args(),
		excludePersonal: *excludePersonal,
		verbose:         *verbose,
	}
	return cfg, &credentials{
		username: userpass[0],
		password: userpass[1],
	}

}

func fetch(pages <-chan int, results chan<- result, creds *credentials) {
	client := &http.Client{
		Timeout: time.Second * 5,
	}
	for page := range pages {
		repos, err := get(client, page, creds)
		if err != nil {
			results <- result{
				err: err,
			}
			return
		}
		if len(repos) == 0 {
			return
		}
		results <- result{
			repos: repos,
		}
	}
}

// get obtains info about repositories at the given page using the given creds.
func get(client *http.Client, page int, creds *credentials) ([]repo, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	q := req.URL.Query()
	q.Add("page", strconv.Itoa(page))
	q.Add("per_page", strconv.Itoa(perPage))
	req.URL.RawQuery = q.Encode()
	if creds != nil {
		req.SetBasicAuth(creds.username, creds.password)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("cannot get %q: %s", req.URL, resp.Status)
	}
	var repos []repo
	d := json.NewDecoder(resp.Body)
	if err = d.Decode(&repos); err != nil {
		return nil, err
	}
	return repos, nil
}

// config holds configuration options.
type config struct {
	query           []string
	verbose         bool
	excludePersonal bool
}

// credentials holds userpass for HTTP basic authentication.
type credentials struct {
	username string
	password string
}

type result struct {
	repos []repo
	err   error
}

// repo holds info about a Github repository.
type repo struct {
	Name string `json:"full_name"`
	Desc string `json:"description"`
	HTTP string `json:"html_url"`
	SSH  string `json:"ssh_url"`
}

// matches reports whether the repo name matches the given query.
func (r repo) matches(query []string) bool {
	name := strings.ToLower(r.Name)
	for _, q := range query {
		if !strings.Contains(name, q) {
			return false
		}
	}
	return true
}

// print outputs info about this repo.
func (r repo) print(verbose bool) {
	if verbose {
		fmt.Printf("%s (%s)\n\t%s\n\t%s\n", r.Name, r.Desc, r.HTTP, r.SSH)
		return
	}
	fmt.Println(r.SSH)
}
