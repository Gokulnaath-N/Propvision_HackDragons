import React, { useState, useCallback, useEffect } from 'react';
import { UploadCloud, Image as ImageIcon, X, Loader2, Sparkles, CheckCircle2, ChevronRight, Building, MapPin, Activity } from 'lucide-react';
import Navbar from '../components/Navbar';
import { uploadImages, getJobStatus } from '../services/api';
import './BrokerUpload.css';

const BrokerUpload = () => {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    bhk: '2',
    city: 'Chennai',
    location: '',
    propertyType: 'apartment',
    vastuCompliant: false
  });

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [pipelineStage, setPipelineStage] = useState(0); 
  const [uploadComplete, setUploadComplete] = useState(false);

  // Handle Drag Events
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  // Handle Drop Event
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  // Handle file input selection
  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = (newFiles) => {
    // Filter only images
    const imageFiles = newFiles.filter(file => file.type.startsWith('image/'));
    if (imageFiles.length === 0) return;

    setFiles(prev => [...prev, ...imageFiles]);
    
    // Generate previews
    const newPreviews = imageFiles.map(file => URL.createObjectURL(file));
    setPreviews(prev => [...prev, ...newPreviews]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => prev.filter((_, i) => i !== index));
  };

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      alert("Please upload at least one image.");
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(10);
    setPipelineStage(1); // Uploading

    try {
      // 1. Submit images and metadata to backend
      const uploadRes = await uploadImages(files, {
        city: formData.city,
        location: formData.location,
        price: formData.price,
        bhk: formData.bhk,
        vastu: formData.vastuCompliant
      }, (progress) => {
        // Adjust progress for just the upload phase (0-30%)
        setUploadProgress(10 + Math.floor(progress * 0.2)); 
      });
      
      const returnedJobId = uploadRes.job_id;
      setJobId(returnedJobId);
      
      // 2. Start polling for job status
      pollJobStatus(returnedJobId);

    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload listing. Please try again.");
      setIsUploading(false);
    }
  };

  const pollJobStatus = async (currentJobId) => {
    try {
      const statusRes = await getJobStatus(currentJobId);
      
      // Map mock backend status to UI stages
      if (statusRes.status === "processing") {
        setUploadProgress(40 + (statusRes.progress * 0.5));
        
        // Fancier mock stages for UI based on progress
        if (statusRes.progress < 30) setPipelineStage(2); // ESRGAN
        else if (statusRes.progress < 60) setPipelineStage(3); // CLIP
        else setPipelineStage(4); // Claude
        
        // Keep polling
        setTimeout(() => pollJobStatus(currentJobId), 1500);
      } else if (statusRes.status === "complete") {
        setUploadProgress(100);
        setPipelineStage(5); // Complete
        
        setTimeout(() => {
          setUploadComplete(true);
        }, 1000);
      }
    } catch (error) {
      console.error("Failed to poll status:", error);
      // Even if polling fails gracefully fallback
      setTimeout(() => pollJobStatus(currentJobId), 2000);
    }
  };

  return (
    <div className="broker-upload-container">
      <Navbar />

      <main className="max-w-4xl mx-auto px-6">
        <div className="upload-header">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="p-2 bg-[rgba(0,200,224,0.1)] rounded-lg text-[#00C8E0]">
              <Building size={20} />
            </div>
            <span className="font-mono text-sm tracking-widest text-[#00C8E0] uppercase">Broker Dashboard</span>
          </div>
          <h1 className="upload-title">New Property Listing</h1>
          <p className="upload-subtitle">
            Upload your property details. High-quality images will be automatically enhanced using Real-ESRGAN and semantically tagged by our AI pipeline.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="upload-card relative z-10">
          
          {/* DRAG AND DROP ZONE */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <label className="font-syne font-semibold text-xl">Property Images <span className="text-red-400">*</span></label>
              <span className="text-sm font-mono text-white/40">{files.length} uploaded</span>
            </div>
            
            <div 
              className={`dropzone ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input 
                type="file" 
                className="file-input-hidden" 
                multiple 
                accept="image/*" 
                onChange={handleChange} 
              />
              <div className="dropzone-icon">
                <UploadCloud size={32} />
              </div>
              <p className="dropzone-title">Drag & drop images here</p>
              <p className="dropzone-desc">or click to browse files (JPEG, PNG, WebP)</p>
            </div>

            {previews.length > 0 && (
              <div className="preview-grid">
                {previews.map((src, idx) => (
                  <div key={idx} className="preview-item">
                    <img src={src} alt="preview" />
                    <button type="button" className="preview-remove" onClick={() => removeFile(idx)}>
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="h-px bg-white/10 w-full my-4"></div>

          {/* AI INFO BANNER */}
          <div className="ai-pipeline-banner">
            <div className="ai-icon-group">
              <Sparkles size={24} />
            </div>
            <div className="ai-text">
              <h4>Intelligent Pipeline Enabled</h4>
              <p>Your listing will be automatically passed through Real-ESRGAN upscaling, CLIP vectorization, and Claude vision analysis before going live.</p>
            </div>
          </div>

          {/* PROPERTY FORM */}
          <div className="form-grid mt-2">
            
            <div className="input-group full-width">
              <label className="form-label">Property Title <span className="text-red-400">*</span></label>
              <input type="text" name="title" className="form-input" placeholder="e.g. Luxury 3BHK in Seawoods" required value={formData.title} onChange={handleFormChange} />
            </div>

            <div className="input-group">
              <label className="form-label">Price (in ₹ Lakhs) <span className="text-red-400">*</span></label>
              <input type="number" name="price" className="form-input" placeholder="e.g. 150" required value={formData.price} onChange={handleFormChange} />
            </div>

            <div className="input-group">
              <label className="form-label">BHK</label>
              <select name="bhk" className="form-select" value={formData.bhk} onChange={handleFormChange}>
                <option value="1">1 BHK</option>
                <option value="2">2 BHK</option>
                <option value="3">3 BHK</option>
                <option value="4">4 BHK</option>
                <option value="4+">4+ BHK / Villa</option>
              </select>
            </div>

            <div className="input-group">
              <label className="form-label">City <span className="text-red-400">*</span></label>
              <select name="city" className="form-select" value={formData.city} onChange={handleFormChange}>
                <option value="Chennai">Chennai</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Bangalore">Bangalore</option>
                <option value="Hyderabad">Hyderabad</option>
                <option value="Delhi">Delhi</option>
              </select>
            </div>

            <div className="input-group">
              <label className="form-label">Neighbourhood / Locality <span className="text-red-400">*</span></label>
              <input type="text" name="location" className="form-input" placeholder="e.g. Anna Nagar" required value={formData.location} onChange={handleFormChange} />
            </div>

            <div className="input-group full-width">
              <label className="form-label">Property Description</label>
              <textarea name="description" className="form-textarea" placeholder="Highlight key features, amenities, and connectivity..." value={formData.description} onChange={handleFormChange}></textarea>
            </div>
            
            <div className="input-group full-width mt-2">
              <label className="checkbox-label">
                <input type="checkbox" name="vastuCompliant" className="checkbox-custom" checked={formData.vastuCompliant} onChange={handleFormChange} />
                Property is Vastu Compliant
              </label>
            </div>

          </div>

          <button type="submit" className="submit-btn" disabled={isUploading || files.length === 0}>
            {isUploading ? <Loader2 className="animate-spin" size={20} /> : <UploadCloud size={20} />}
            {isUploading ? 'Processing & Enhancing...' : 'Process & Publish Listing'}
          </button>
        </form>

        {/* RECENT UPLOADS SECTION */}
        {!isUploading && (
          <div className="mt-20 mb-20 animate-in fade-in slide-in-from-bottom-10 duration-1000 delay-200">
            <div className="flex items-center justify-between mb-8">
              <h2 className="display-font text-2xl font-bold">Your Recent Listings</h2>
              <button className="text-sm font-mono text-[#00C8E0] hover:underline cursor-pointer bg-transparent border-none">View All Listings</button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                { 
                  id: '1', title: 'Modern 3BHK Apartment', location: 'Anna Nagar, Chennai', price: '₹1.2 Cr', 
                  image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=400&auto=format&fit=crop',
                  status: 'Active', rooms: 3, score: 92
                },
                { 
                  id: '2', title: 'Luxury Villa with Pool', location: 'OMR, Chennai', price: '₹3.5 Cr', 
                  image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?q=80&w=400&auto=format&fit=crop',
                  status: 'Active', rooms: 5, score: 96
                }
              ].map(property => (
                <div key={property.id} className="bg-[#0A0E20] border border-white/10 rounded-2xl overflow-hidden hover:border-[#3B6FFF]/50 transition-all group">
                  <div className="flex p-4 gap-4">
                    <div className="w-24 h-24 rounded-xl overflow-hidden shrink-0 border border-white/5">
                      <img src={property.image} alt={property.title} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                    </div>
                    <div className="flex-1 flex flex-col justify-between overflow-hidden">
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <h4 className="font-syne font-bold text-base truncate">{property.title}</h4>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{property.status}</span>
                        </div>
                        <p className="text-xs text-white/50 flex items-center gap-1">
                          <MapPin size={12} /> {property.location}
                        </p>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-[#00C8E0] font-bold text-sm">{property.price}</span>
                        <div className="flex items-center gap-3">
                          <div className="flex flex-col items-end">
                            <span className="text-[9px] font-mono text-white/30 uppercase">AI Score</span>
                            <span className="text-xs font-bold text-white/90">{property.score}%</span>
                          </div>
                          <ChevronRight size={16} className="text-white/20 group-hover:text-[#3B6FFF] transition-colors" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-8 p-6 rounded-2xl bg-[#3B6FFF]/5 border border-[#3B6FFF]/10 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[#3965ff]/20 text-[#3B6FFF] flex items-center justify-center">
                  <Activity size={24} />
                </div>
                <div>
                  <h4 className="text-sm font-semibold">Account Statistics</h4>
                  <p className="text-xs text-white/50">Your listings have received 1,240 views today.</p>
                </div>
              </div>
              <div className="flex gap-8">
                <div className="text-center">
                  <div className="text-xl font-bold">12</div>
                  <div className="text-[10px] font-mono text-white/40 uppercase">Total</div>
                </div>
                <div className="text-center border-l border-white/10 pl-8">
                  <div className="text-xl font-bold">4.8</div>
                  <div className="text-[10px] font-mono text-white/40 uppercase">Avg Rating</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* UPLOAD PROGRESS MODAL */}
      {isUploading && (
        <div className="upload-progress-overlay">
          <div className="upload-progress-card animate-in zoom-in-95 duration-300">
            
            {uploadComplete ? (
              <div className="flex flex-col items-center">
                <div className="w-20 h-20 bg-emerald-500/20 text-emerald-500 rounded-full flex items-center justify-center mb-6 animate-in zoom-in duration-500">
                  <CheckCircle2 size={40} />
                </div>
                <h3 className="progress-title text-emerald-400">Listing Published!</h3>
                <p className="text-white/60 mb-8 mt-2">The property has been successfully enhanced and added to the semantic search database.</p>
                <button 
                  onClick={() => window.location.reload()} 
                  className="bg-white text-black px-6 py-3 rounded-full font-semibold hover:bg-gray-200"
                >
                  Upload Another
                </button>
              </div>
            ) : (
              <>
                <div className="processing-icon">
                  <div className="pulse-ring"></div>
                  <div className="pulse-ring"></div>
                  <div className="processing-icon-inner">
                    <Sparkles size={32} />
                  </div>
                </div>
                
                <h3 className="progress-title">AI Processing</h3>
                <div className="progress-status">
                  {pipelineStage === 1 && "Uploading images to server..."}
                  {pipelineStage === 2 && "Real-ESRGAN enhancing details..."}
                  {pipelineStage === 3 && "CLIP extracting semantic vectors..."}
                  {pipelineStage === 4 && "Claude analyzing room structure..."}
                </div>

                <div className="progress-bar-container">
                  <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }}></div>
                </div>

                <div className="progress-steps mt-6">
                  <div className={`progress-step ${pipelineStage > 1 ? 'completed' : pipelineStage === 1 ? 'active' : ''}`}>
                    <div className="step-circle">{pipelineStage > 1 ? <CheckCircle2 size={12}/> : ''}</div> 
                    Secure Upload
                  </div>
                  <div className={`progress-step ${pipelineStage > 2 ? 'completed' : pipelineStage === 2 ? 'active' : ''}`}>
                    <div className="step-circle">{pipelineStage > 2 ? <CheckCircle2 size={12}/> : ''}</div> 
                    Real-ESRGAN Upscaling
                  </div>
                  <div className={`progress-step ${pipelineStage > 3 ? 'completed' : pipelineStage === 3 ? 'active' : ''}`}>
                    <div className="step-circle">{pipelineStage > 3 ? <CheckCircle2 size={12}/> : ''}</div> 
                    CLIP Semantic Vectorization
                  </div>
                  <div className={`progress-step ${pipelineStage > 4 ? 'completed' : pipelineStage === 4 ? 'active' : ''}`}>
                    <div className="step-circle">{pipelineStage > 4 ? <CheckCircle2 size={12}/> : ''}</div> 
                    Claude Room Classification
                  </div>
                </div>
              </>
            )}

          </div>
        </div>
      )}
    </div>
  );
};

export default BrokerUpload;
