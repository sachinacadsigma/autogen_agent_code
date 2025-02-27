from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS
# from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
import os
import tempfile
# import faiss  # FAISS dependency
import pickle  # For custom serialization
# from langchain_huggingface import HuggingFaceEmbeddings

# Embedding model setup (using SentenceTransformer)
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Flask app setup
app = Flask(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Flask route for processing documents
@app.route('/process_doc', methods=['POST'])
def process_document():
    # Validate input
    if 'document' not in request.files or 'employee_id' not in request.form:
        return jsonify({"error": "Missing document or employee number"}), 400

    file = request.files['document']
    employee_id = request.form['employee_id']

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Only PDF and DOCX are allowed."}), 400

    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file.read())
        temp_file.close()  # Close the temp file to be used later

        # Now load the document from the temporary file
        try:
            if file.filename.endswith('.pdf'):
                loader = PyPDFLoader(temp_file.name)  # Use the temporary file
            elif file.filename.endswith('.docx'):
                loader = Docx2txtLoader(temp_file.name)  # Use the temporary file
            else:
                return jsonify({"error": "Unsupported file type"}), 400

            documents = loader.load()
        except Exception as e:
            return jsonify({"error": f"Error loading document: {str(e)}"}), 500

        # After processing the document, remove the temporary file
        os.remove(temp_file.name)

    # Split the document into smaller chunks for embedding
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
    splits = text_splitter.split_documents(documents)

    # Create FAISS vectorstore with embedded chunks
    try:
        vectorstore = FAISS.from_documents(splits, embedding_model)  # Use FAISS instead of Chroma
    except Exception as e:
        return jsonify({"error": f"Error creating vectorstore: {str(e)}"}), 500

    # Serialize the FAISS vectorstore object using pickle
    try:
        # Save the serialized vectorstore to a file on the server's disk
        vectorstore_filename = f"vectorstore_{employee_id}.pkl"  # Create a unique filename based on employee number
        vectorstore_filepath = os.path.join('vectorstores', vectorstore_filename)

        # Ensure the directory exists
        os.makedirs('vectorstores', exist_ok=True)

        with open(vectorstore_filepath, 'wb') as f:
            pickle.dump(vectorstore, f)

    except Exception as e:
        return jsonify({"error": f"Error saving vectorstore: {str(e)}"}), 500

    # Convert the query to embedding and perform semantic search
    query = "Vacation policy"  # You can change this to dynamic queries as per your need
    try:
        query_embedding = embedding_model.embed_query(query)
        
        # Load the vectorstore from disk to perform the search
        with open(vectorstore_filepath, 'rb') as f:
            vectorstore = pickle.load(f)

        results = vectorstore.similarity_search_by_vector(query_embedding, k=2)

        # Format and return the results
        # result_chunks = [{"text": result.page_content, "embedding": embedding_model.embed_documents([result.page_content])[0]} for result in results]
        result_chunks = [{"text": result.page_content} for result in results]

    except Exception as e:
        return jsonify({"error": f"Error during semantic search: {str(e)}"}), 500

    return jsonify({"results": result_chunks, "employee_id": employee_id})

if __name__ == '__main__':
    app.run(debug=True)
