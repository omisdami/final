let currentDocumentUUID = null;

// For dropdown customization
const CUSTOMIZE_VALUE = "__customize__";
let lastTemplate = "";   // remembers the last real selection

// ============================================================
// Utility Functions
// ============================================================

// Reveal sections on scroll
const fadeSections = document.querySelectorAll('.fade-section');
const revealOnScroll = () => {
  const trigger = window.innerHeight * 0.85;
  fadeSections.forEach(section => {
    const top = section.getBoundingClientRect().top;
    if (top < trigger) section.classList.add('visible');
  });
}
window.addEventListener('scroll', revealOnScroll);
revealOnScroll(); // initial call

// Remove style example
function removeStyleExample() {
  document.getElementById("exampleFile").value = "";
  document.getElementById("stylePreview").classList.add("d-none");
  updateProgressBar(1, "Step 1: Upload Reference Material/s (.DOCX/.PDF)");
}

// Upload and process files
async function uploadFile() {
  const fileInput = document.getElementById("docFile");
  const templateSelect = document.getElementById("templateSelect");
  const exampleFileInput = document.getElementById("exampleFile");
  
  if (fileInput.files.length === 0) {
    alert("Please select at least one reference document.");
    return;
  }
  
  if (!templateSelect.value) {
    alert("Please select a template.");
    return;
  }
  
  updateProgressBar(2, "Step 2: Processing Documents...");
  
  const formData = new FormData();
  
  // Add reference files
  for (let file of fileInput.files) {
    formData.append("files", file);
  }
  
  // Add template
  formData.append("template_name", templateSelect.value);
  
  // Add example file if available
  if (exampleFileInput.files[0]) {
    formData.append("example_file", exampleFileInput.files[0]);
  }
  
  try {
    const response = await fetch("/documents/process/", {
      method: "POST",
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log("Upload API response:", result);
    
    currentDocumentUUID = result.uuid;
    
    const sections = Object.values(result.flattened_sections);
    
    let fullReport = "";
    const parentMap = {};
    
    for (const section of sections) {
      const parent = section.parent_title || null;
      const title = section.title || "";
      const content = section.content || "";
      
      if (parent) {
        if (!parentMap[parent]) {
          parentMap[parent] = [];
        }
        parentMap[parent].push({ title, content });
      } else {
        fullReport += `# ${title}\n\n${content}\n\n`;
      }
    }
    
    for (const [parentTitle, children] of Object.entries(parentMap)) {
      fullReport += `# ${parentTitle}\n\n`;
      for (const child of children) {
        fullReport += `## ${child.title}\n\n${child.content}\n\n`;
      }
    }
    
    document.getElementById("docContent").value = fullReport.trim();
    
    const renderedHTML = marked.parse(fullReport.trim());
    document.getElementById("chatWindow").innerHTML = renderedHTML;
    
    document.getElementById("chatSection").style.display = "block";
    document.getElementById("downloadLinks").classList.remove("d-none");
    document.getElementById("feedbackSection").classList.remove("d-none");
    
    updateDownloadLinks(result.docx_path, result.pdf_path);
    
    updateProgressBar(3, "Step 3: Report Generated Successfully!");
    
  } catch (error) {
    console.error("Processing failed:", error);
    alert("Failed to process documents. Please try again.");
    updateProgressBar(1, "Step 1: Upload Reference Material/s (.DOCX/.PDF)");
  }
}

// Update progress bar
function updateProgressBar(step, text) {
  const progressBar = document.getElementById("progressBar");
  const percentage = (step / 3) * 100;
  
  progressBar.style.width = `${percentage}%`;
  progressBar.textContent = text;
  
  // Update color based on step
  progressBar.className = "progress-bar progress-step";
  if (step === 3) {
    progressBar.classList.add("bg-success");
  } else if (step === 2) {
    progressBar.classList.add("bg-warning");
  }
}


// Format report text (from original app.js)
function formatReportText(text) {
  // Remove 'TERMINATE'
  text = text.replace(/TERMINATE/g, "").trim();

  // Split the input into lines
  const lines = text.split("\n");

  let html = "";
  for (let line of lines) {
    const trimmed = line.trim();

    if (!trimmed) {
      // Skip empty lines (for spacing)
      html += "<br>";
      continue;
    }

    if (/^# (.+)/.test(trimmed)) {
      // Convert Markdown-style header to <h4>
      const heading = trimmed.replace(/^# (.+)/, '<h4 class="mt-3 mb-2">$1</h4>');
      html += heading;
    } else {
      // Wrap normal lines in <p>
      html += `<p>${trimmed}</p>`;
    }
  }

  return html;
}

/**
 * Appends a message to the chat window.
 */
function appendChat(role, message) {
  const chatWindow = document.getElementById("chatWindow");
  const msgContainer = document.createElement("div");

  const formatted = role === "bot" ? formatReportText(message) : `<p>${message}</p>`;
  msgContainer.innerHTML = `<div class="chat-msg ${role}">${formatted}</div>`;

  chatWindow.appendChild(msgContainer);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * Update DOCX and PDF download links and reveal the download section.
 */
function updateDownloadLinks(docx, pdf) {
  const docxName = docx.split("/").pop();
  const pdfName = pdf.split("/").pop();

  const docxLink = document.getElementById("docxLink");
  const pdfLink = document.getElementById("pdfLink");

  // Ensure correct paths
  const docxPath = docx.startsWith("/") ? docx : `/${docx}`;
  const pdfPath = pdf.startsWith("/") ? pdf : `/${pdf}`;

  docxLink.href = docxPath;
  docxLink.download = docxName;

  pdfLink.href = pdfPath;
  pdfLink.download = pdfName;

  document.getElementById("downloadLinks").classList.remove("d-none"); // Show the download section
}

/**
 * Remove selected file and reset UI elements to initial state.
 */
function removeFile() {
  document.getElementById("docFile").value = "";
  document.getElementById("filePreview").classList.add("d-none");
  updateProgressBar(1, "Step 1: Upload Reference Material/s (.DOCX/.PDF)");
}

// ============================================================
// Template Handling
// ============================================================

/**
 * Load available document templates and populate the dropdown.
 */
async function loadTemplateOptions() {
  try {
    const res = await fetch("/documents/templates/");
    if (!res.ok) throw new Error("Failed to fetch templates");
    const data = await res.json();

    const templateSelect = document.getElementById("templateSelect");
    templateSelect.innerHTML = "";

    // Only keep real templates (hide the schema file)
    const names = (data.available_templates || []).filter(
      (n) => n && n !== "template_schema.json"
    );

    if (names.length > 0) {
      for (const name of names) {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name.replace(/_/g, " ").replace(".json", "");
        templateSelect.appendChild(opt);
      }

      // The special action item at the end
      const customize = document.createElement("option");
      customize.value = CUSTOMIZE_VALUE;
      customize.textContent = "Customize template";
      templateSelect.appendChild(customize);

      // Default to first real template; remember it
      templateSelect.value = names[0];
      lastTemplate = templateSelect.value;
    } else {
      const opt = document.createElement("option");
      opt.textContent = "No templates available";
      opt.disabled = true;
      templateSelect.appendChild(opt);
    }
  } catch (error) {
    alert("Error loading templates: " + error.message);
  }
}

function onTemplateChange(e) {
  const sel = e.target;
  const val = sel.value;

  if (val === CUSTOMIZE_VALUE) {
    // Open the Template Editor for the currently selected real template
    const target = lastTemplate || "proposal_template.json";
    window.open(`/template-editor?name=${encodeURIComponent(target)}`, "_blank");

    // Revert the dropdown to the last real template so the action item isn't "stuck"
    sel.value = lastTemplate;
    return;
  }

  // User picked a real template — remember it
  lastTemplate = val;
}

// ============================================================
// Chat Functions
// ============================================================
async function sendQuestion() {
  const docContent = document.getElementById("docContent").value;
  const question = document.getElementById("userInput").value;

  if (!question.trim()) return;

  appendChat("user", question);
  document.getElementById("userInput").value = "";

  try {
    const res = await fetch("/documents/chat/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_content: docContent, question: question })
    });

    if (!res.ok) {
      const text = await res.text();
      alert("Chat request failed: " + text);
      return;
    }

    const result = await res.json();
    console.log("Chat API response:", result);

    const reply = (result.answer || "No response.").replace(/TERMINATE/g, "");

    currentDocumentUUID = result.uuid || currentDocumentUUID;

    // Format reply as Markdown → HTML
    const formattedReply = reply.trim();
    const renderedHTML = marked.parse(formattedReply);

    // Append raw markdown to textarea (history)
    document.getElementById("docContent").value += "\n\n" + formattedReply;

    // Append formatted HTML to chat window
    const chatWindow = document.getElementById("chatWindow");
    const botMsgDiv = document.createElement("div");
    botMsgDiv.classList.add("chat-msg", "bot", "mb-3");
    botMsgDiv.innerHTML = renderedHTML;
    chatWindow.appendChild(botMsgDiv);

    // Auto-scroll to bottom
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Reveal feedback section if hidden
    document.getElementById("chatSection").style.display = "block";
    document.getElementById("feedbackSection").classList.remove("d-none");

    // Update download links if provided
    if (result.docx_path && result.pdf_path) {
      updateDownloadLinks(result.docx_path, result.pdf_path);
    }

  } catch (error) {
    alert("Error sending question: " + error.message);
  }
}

// ============================================================
// Rating & Feedback
// ============================================================

function submitRating(rating) {
  const content = document.getElementById("docContent").value;
  const template = document.getElementById("templateSelect").value;

  const payload = {
    rating: rating,
    document_content: content,
    template_name: template,
    timestamp: new Date().toISOString(),
    uuid: currentDocumentUUID
  };

  fetch("/documents/feedback/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then((res) => {
      if (res.ok) {
        alert(`Thanks for rating this report ${rating}/5!`);
      } else {
        alert("Failed to submit feedback.");
      }
    })
    .catch((err) => {
      console.error("Feedback error:", err);
      alert("Error sending feedback.");
    });
}

// ============================================================
// Initialization
// ============================================================

// Initialize when DOM is loaded
window.addEventListener("DOMContentLoaded", () => {
  loadTemplateOptions();
  
  // Wire the change handler for the dropdown
  const sel = document.getElementById("templateSelect");
  if (sel) sel.addEventListener("change", onTemplateChange);
  
  // Add file preview functionality for reference documents
  document.getElementById("docFile").addEventListener("change", function() {
    const files = this.files;
    if (files.length > 0) {
      const fileNames = Array.from(files).map(f => f.name).join(", ");
      document.getElementById("fileName").textContent = `${files.length} file(s): ${fileNames}`;
      document.getElementById("filePreview").classList.remove("d-none");
    }
  });
  
  // Add file preview functionality for style example
  document.getElementById("exampleFile").addEventListener("change", function() {
    const file = this.files[0];
    if (file) {
      document.getElementById("styleFileName").textContent = file.name;
      document.getElementById("stylePreview").classList.remove("d-none");
    } else {
      document.getElementById("stylePreview").classList.add("d-none");
    }
  });
  
  // Add enter key support for chat
  document.getElementById("userInput").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
      sendQuestion();
    }
  });
  
  revealOnScroll();
});

