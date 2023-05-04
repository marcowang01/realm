import { useEffect, useState } from 'react';
import useSWR from 'swr';

import Head from 'next/head'
import { Inter } from 'next/font/google'
import styles from '@/styles/Home.module.css'

import { ChromaClient, Collection } from 'chromadb';

const inter = Inter({ subsets: ['latin'] })

const NAME = 'alpaca';
const PATH = 'alpaca_small.json'
const QUERY = 'I want to learn how to cook';
const SERVER_ADDR = 'http://localhost:8000';
const logLength = 10;
const SAFE_MODE = true;

export default function Home() {
  const [collection, setCollection] = useState<Collection | null>(null);
  const [client, setClient] = useState<ChromaClient | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  function log(msg: string) {
    if (logs.length > logLength) {
      setLogs([...logs.slice(1), msg]);
    } else {
      setLogs([...logs, msg]);
    }
    console.log(msg);
  }
  
  useEffect(() => {
    setClient(new ChromaClient(SERVER_ADDR));
  }, []);

  // const fetcher = (endpoint: string) => fetch(endpoint).then((res) => res.json())
  const fetcher = async (endpoint: string, options?: RequestInit) => {
    const res = await fetch(endpoint, options);
    return await res.json();
  }
  // caliing the hello api
  async function handleHello(name: string) {
    try {
      log(`calling hello api with name ${name}...`)
      const body = await fetcher("/api/hello", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      log(`hello response: ${body['message']}`)
    } catch (err) {
      log(`Error: ${err}`)
    }
  }

  // create collection instance on the server
  async function handleCreateCollection(name: string, address: string) {
    if (!client) {
      log("client not initialized")
      return;
    }
    try {
      log(`creating collection ${name}...`)
      fetcher(`/api/createCollection?name=${name}&address=${address}`)
        .then((res) => {
          console.log(res)
          if (res['success']) {
            log(`create [${name}] collection success at [${address}]`)
          } else {
            log(`create [${name}] collection failed at [${address}]`)
          }
        })
    } catch (error) {
      log("failed to create collection")
      console.log(error)
    }
  }

  // get instance of collection if it is already created
  async function handleGetCollection(name: string) {
    if (!client) {
      log("client not initialized")
      return;
    }
    log(`getting collection ${name}`)
    const newCollection = await client.getCollection(name);
    console.log(newCollection)
    if (newCollection) {
      setCollection(newCollection);
      log(`get [${name}] collection success`)
    } else {
      log(`get [${name}] collection failed`)
    }
  }
  
  // list all collections
  async function handleListCollections() {
    if (!client) {
      log("client not initialized")
      return;
    }
    log("listing collections")
    const res = await client.listCollections();
    // const res = await collection?.count();
    if (res && res['error']) {
      log("list collections failed")
      console.log(res['error'])
    } else {
      let names = []
      for (let i = 0; i < res.length; i++) {
        names.push(res[i]['name'])
      }
      log(`collections: [${names}]`)
    }
  }

    // count all collections
    async function handleCountCollection() {
      if (!collection) {
        log("no collection found")
        return;
      }
      log("counting collection...")
      try {
        const res = await collection.count();
        if (res && res['error']) {
          log("list collections failed")
          console.log(res['error'])
        } else {
          log(`collections [${collection.name}] has [${res}] items`)
        }
      } catch (error) {
        log("count collection error")
        console.log(error)
      }
    }

    // peek  collections
    async function handlePeekCollection() {
      if (!collection) {
        log("no collection found")
        return;
      }
      log("peeking collections...")
      try {
        const res = await collection.peek();
        // console.log(res)
        if (res && res['error']) {
          log("list collections failed")
          console.log(res['error'])
        } else {
          let results: string[] = []
          for (let i = 0; i < res['documents'].length; i++) {
            results.push(res['documents'][i].slice(15, 160))
          }
          setLogs(results)
        }
      } catch (error) {
        log("peek collection error")
        console.log(error)
      }
    }
  
  // add support to add from json object or file object
  // add to collection (args: name of collection, server address, path to json data)
  async function handleAddToCollection(name: string, address: string, filename: string) {
    if (!collection) {
      log("no collection found")
      return;
    }
    if (SAFE_MODE) {
      log('safe mode enabled, not adding to collection')
      return;
    };
    try {
      console.log("fetching file data from api and adding to collection...")
      fetcher(`/api/addToCollection?name=${name}&address=${address}&filename=${filename}`)
        .then((res) => {
          console.log(res)
          if (res['success']) {
            log(`add to [${name}] collection success at [${address}] with file [${filename}]`)
          } else if (res['error']) {
            log(`add to [${name}] collection failed at [${address}] with file [${filename}]`)
          }
        })
    } catch (error) {
      log("failed to add to collection")
      console.log(error)
    }
  }

  // query collection (args: name of collection, server address, query text, number of results)
  async function handleQueryCollection(name: string, address: string, query: string, n: number) {
    if (!collection) {
      log("no collection found")
      return;
    }
    try {
      console.log("querying collection...")
      fetcher(`/api/queryCollection?name=${name}&address=${address}&text=${query}&n=${n}`)
        .then((res) => {
          if (res['data']) {
            const queryResults = res.data.documents[0]
            let results: string[] = []
            for (let i = 0; i < queryResults.length; i++) {
              results.push(queryResults[i].slice(15, 160))
            }
            setLogs(results)
          } else if (res['error']) {
            log(`add to [${name}] collection failed at [${address}] with query [${query}]`)
          }
        })
    } catch (error) {
      log("failed to add to collection")
      console.log(error)
    }
  }

  // delete collection
  async function handleDeleteCollection(name: string) {
    if (!client) {
      log("client not initialized")
      return;
    }
    if (SAFE_MODE) {
      log('safe mode enabled, not deleting collection')
      return;
    };
    log(`deleting collection ${name}`)
    try {
      const res = await client.deleteCollection(name);
      if (res && res['error']) {
        log(`delete ${name} collection failed`)
        console.log(res['error'])
      } else {
        log(`delete ${name} collection success`)
      }
    } catch (error) {
      log(`delete ${name} collection error`)
      console.log(error)
    }
  }


  return (
    <>
      <Head>
        <title>Instruction DB</title>
        <meta name="description" content="instruction DB" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className={`${styles.main} ${inter.className}`}>
        <h2>{collection? `Collection: ${collection.name} ` : "No Collection Found"}</h2>
        <div className={styles.grid}>
          <div
            className={styles.card}
            // onClick={() => handleCreateCollection(NAME, SERVER_ADDR)}
            onClick={() => handleHello(NAME)}
          >
            <h2>
              create <span>-&gt;</span>
            </h2>
          </div>
          <div
            className={styles.card}
            onClick={() => handleGetCollection(NAME)}
          >
            <h2>
              get <span>-&gt;</span>
            </h2>
          </div>
          <div
            className={styles.card}
            onClick={() => handleListCollections()}
          >
            <h2>
              list <span>-&gt;</span>
            </h2>
          </div>
          <div
            className={styles.card}
            onClick={() => handleCountCollection()}
          >
            <h2>
              count <span>-&gt;</span>
            </h2>
          </div>
          <div
            className={styles.card}
            onClick={() => handlePeekCollection()}
          >
            <h2>
              peek <span>-&gt;</span>
            </h2>
          </div>
          <div
            className={styles.card}
            onClick={() => handleAddToCollection(NAME, SERVER_ADDR, PATH)}
          >
            <h2>
              add <span>-&gt;</span>
            </h2>
          </div>
          <div
            className={styles.card}
            onClick={() => handleQueryCollection(NAME, SERVER_ADDR, QUERY, logLength)}
          >
            <h2>
              query <span>-&gt;</span>
            </h2>
          </div>
          <div
            className={styles.card}
            onClick={() => handleDeleteCollection(NAME)}
          >
            <h2>
              delete <span>-&gt;</span>
            </h2>
          </div>
        </div>
        {logs.map((log, i) => {
          return (
          <p 
            key={`log${i}`} 
            style={{ 
              whiteSpace: "pre-wrap", 
              width: "90%", 
              textAlign: "left", 
              marginTop: "0.2em"
            }}>
            {`% ${log}`}
          </p>
          )
        })}
      </main>
    </>
  )
}
