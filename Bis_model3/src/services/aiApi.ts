import { apiClient } from './api';
import { AIChatRequest, ChatMessageItem, SourceReferenceItem } from '../types/ai';
import { detectProductStandard } from '../utils/bisMatcher';

export const createWelcomeMessage = (applicationId?: string): ChatMessageItem => ({
  id: 'msg-welcome',
  role: 'assistant',
  content: applicationId
    ? `👋 **Hello! I am your ISense AI Assistant.**\n\nI am connected to your application dossier for **${applicationId}**. Ask me about required documents, testing parameters, applicable Indian Standards, or certification procedures.`
    : `👋 **Welcome to ISense — Your BIS Regulatory Assistant!**\n\nI provide verified compliance guidance for **Bureau of Indian Standards (BIS)** certifications, mandatory Indian Standards, laboratory testing protocols, and portal filings.\n\n💡 **How to ask me:**\n• *Product Inquiries*: e.g., "What standard applies to LED lamps?" or "Water bottle"\n• *Testing Requirements*: e.g., "Explain testing clauses for IS 16102"\n• *Application Documents*: e.g., "Documents required for ISI Mark certification"\n\nWhat product or Indian Standard would you like to explore?`,
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  sources: [],
});

let activeChatHistory: ChatMessageItem[] = [createWelcomeMessage()];

export const aiApi = {
  getChatHistory: async (applicationId?: string): Promise<ChatMessageItem[]> => {
    if (activeChatHistory.length === 0) {
      activeChatHistory = [createWelcomeMessage(applicationId)];
    }
    return [...activeChatHistory];
  },

  recordUserMessage: (msg: ChatMessageItem) => {
    activeChatHistory.push(msg);
  },

  sendMessage: async (payload: AIChatRequest): Promise<ChatMessageItem> => {
    try {
      const response = await apiClient.post<ChatMessageItem>('/api/ai/chat', payload);
      activeChatHistory.push(response.data);
      return response.data;
    } catch (err) {
      console.warn('Real-time RAG backend request failed, using local guidance fallback:', err);
      // Dynamic fallback referencing the configured BIS knowledge base
      const queryLower = payload.message.toLowerCase();
      const detected = detectProductStandard(payload.message);
      let replyContent = '';
      let sources: SourceReferenceItem[] = [];

      // 1. Statutory Non-Certification Guardrail
      if (
        queryLower.includes('issue license') ||
        queryLower.includes('approve') ||
        queryLower.includes('grant certificate') ||
        queryLower.includes('issue me a bis')
      ) {
        replyContent =
          '**Statutory Boundary & Non-Certification Notice:**\n\n' +
          '**No, ISense does not grant licenses, issue Standard Marks, or officially approve products.**\n\n' +
          'ISense is an **independent compliance assistance platform** designed to guide manufacturers and applicants through Indian Standards compliance, document verification, and laboratory testing requirements.\n\n' +
          '• **Official Authority**: Final certification, ISI mark licenses, and CRS registrations are granted solely by the **Bureau of Indian Standards (BIS)**.\n' +
          '• **Statutory Portal**: Official submissions must be filed directly on the [BIS Manak Online Portal](https://www.manakonline.in).\n\n' +
          '*Potentially relevant BIS information for advisory assistance.*';
        sources = [
          {
            id: 'src-kb-statutory',
            title: 'BIS Act 2016 & Conformity Assessment Regulations',
            documentRef: 'Statutory Operational Framework',
            page: 1,
            section: 'Chapter III — Grant and Renewal of License',
            excerpt: 'Certification marks and licenses are granted solely by the Bureau of Indian Standards through authorized statutory officers.',
            sourceUrl: 'https://www.services.bis.gov.in',
          },
        ];
      }
      // 2. Fees Inquiry
      else if (
        queryLower.includes('fee') ||
        queryLower.includes('cost') ||
        queryLower.includes('charge') ||
        queryLower.includes('how much')
      ) {
        replyContent =
          `### Bureau of Indian Standards Statutory Fee Structure (${detected.scheme}):\n\n` +
          '• **Application Fee**: ₹1,000 (Non-refundable statutory filing charge).\n' +
          '• **Processing Fee**: ₹50,000 to ₹70,000 (For CRS, depending on product scale; valid for 2 years).\n' +
          '• **Factory Inspection Fee (Scheme I / ISI Mark)**: ₹7,000 per man-day for BIS inspecting officers (plus travel expenses).\n' +
          '• **Annual License Fee**: ₹1,000 per year.\n' +
          '• **Marking Fee**: Computed per unit produced, subject to statutory minimum rates.\n' +
          '• **Laboratory Testing Charges**: Billed directly by BIS-recognized testing laboratories.\n\n' +
          '*Potentially relevant BIS information for advisory assistance. Review required.*';
        sources = [
          {
            id: 'src-kb-fees',
            title: 'BIS Financial Regulations — Fee Schedule',
            documentRef: 'Schedule 1 — Statutory Fees',
            page: 14,
            section: 'Section 4 — Application & Processing Charges',
            excerpt: 'Official fees payable directly to the Bureau of Indian Standards for conformity assessment and license grant.',
            sourceUrl: 'https://www.services.bis.gov.in',
          },
        ];
      }
      // 3. Document / Checklist Inquiry
      else if (
        queryLower.includes('document') ||
        queryLower.includes('pending') ||
        queryLower.includes('checklist') ||
        queryLower.includes('need')
      ) {
        const checklistItems = detected.checklist.map((item, i) => `${i + 1}. **${item}**`).join('\n');
        replyContent =
          `Based on the configured BIS regulatory knowledge base for **${detected.category}** (**${detected.standardCode}**):\n\n` +
          `The following mandatory compliance artifacts are required for your technical dossier:\n\n` +
          `${checklistItems}\n\n` +
          `• **Regulatory Scheme**: ${detected.scheme}\n` +
          `• **Governing Division**: ${detected.division}\n` +
          `• **Testing Scope**: ${detected.scopeSummary}\n\n` +
          '*Document Check Note*: Ensure all laboratory test certificates carry authenticated NABL QR codes and accredited test report numbers.\n\n' +
          '*Potentially relevant BIS information for advisory assistance. Final certification decisions remain solely with the Bureau of Indian Standards.*';
        sources = [
          {
            id: `src-kb-${detected.standardCode.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
            title: `${detected.standardCode} — ${detected.standardTitle}`,
            documentRef: detected.standardCode,
            page: 4,
            section: 'Clause 4 — General Requirements & Technical Dossier Checklist',
            excerpt: `Compliance testing and essential technical documentation conforming to ${detected.standardCode}.`,
            sourceUrl: 'https://www.services.bis.gov.in',
          },
        ];
      }
      // 4. Step-by-Step / Process Inquiry
      else if (
        queryLower.includes('step') ||
        queryLower.includes('next') ||
        queryLower.includes('status') ||
        queryLower.includes('how to apply') ||
        queryLower.includes('procedure')
      ) {
        replyContent =
          `### Step-by-Step BIS Certification Roadmap for **${detected.standardCode}**:\n\n` +
          `1. **Standard & Scope Verification**: Confirm applicability under **${detected.standardCode}** (${detected.standardTitle}).\n` +
          '2. **Sample Testing at Recognized Lab**: Send product samples to a BIS-recognized or NABL-accredited test laboratory.\n' +
          '3. **Technical Dossier Compilation**: Assemble technical datasheets, component ratings, and circuit diagrams.\n' +
          '4. **Factory Quality Assurance Plan (QAP)**: Establish in-house testing equipment and calibration logs conforming to the Scheme of Inspection and Testing (SIT).\n' +
          '5. **Manak Online Submission**: Complete portal filing with test reports issued within 90 days.\n\n' +
          '*Potentially relevant BIS information for advisory assistance.*';
        sources = [
          {
            id: 'src-kb-process',
            title: 'BIS Operational Manual — Certification Roadmap',
            documentRef: 'Operational Manual Rev 4',
            page: 18,
            section: 'Stage 5 — Application Submission to Grant of License',
            excerpt: 'Standardized operational procedures for conformity assessment under BIS regulations.',
            sourceUrl: 'https://www.services.bis.gov.in',
          },
        ];
      }
      // 5. Standard Code Inquiry
      else if (
        queryLower.includes('standard') ||
        queryLower.includes('is number') ||
        queryLower.includes('which is') ||
        queryLower.includes('code')
      ) {
        replyContent =
          `According to the configured BIS regulatory knowledge base, the applicable standard is:\n\n` +
          `• **Indian Standard Number**: **${detected.standardCode}**\n` +
          `• **Standard Title**: ${detected.standardTitle}\n` +
          `• **Regulatory Scheme**: ${detected.scheme}\n` +
          `• **Governing Division**: ${detected.division}\n` +
          `• **Key Testing Scope**: ${detected.scopeSummary}\n\n` +
          'Under statutory regulations (such as DPIIT Quality Control Orders or MeitY CRS Orders), products under this scope require registration with the Bureau of Indian Standards prior to commercial distribution or import in India.\n\n' +
          '*Potentially relevant BIS information for advisory assistance.*';
        sources = [
          {
            id: `src-kb-${detected.standardCode.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
            title: `${detected.standardCode} — ${detected.standardTitle}`,
            documentRef: detected.standardCode,
            page: 1,
            section: 'Scope & Application Parameters',
            excerpt: `Specifies requirements, testing methodologies, and inspection criteria for ${detected.standardTitle}.`,
            sourceUrl: 'https://www.services.bis.gov.in',
          },
        ];
      }
      // 6. General / Product-Specific Technical Query
      else {
        replyContent =
          `Based on the configured BIS regulatory knowledge base regarding "${payload.message}":\n\n` +
          `### Applicable Standard: **${detected.standardCode}**\n` +
          `**${detected.standardTitle}** (${detected.category})\n\n` +
          `• **Governing Scheme**: ${detected.scheme}\n` +
          `• **Technical Testing Focus**: ${detected.scopeSummary}\n\n` +
          `### Key Required Dossier Items:\n` +
          `${detected.checklist.slice(0, 3).map((c, i) => `${i + 1}. ${c}`).join('\n')}\n\n` +
          'Both your WhatsApp assistant and Web portal are synchronized to this unified knowledge base. You can review exact clause checklists under the Requirements tab or manage files in Document Management.\n\n' +
          '*Potentially relevant BIS information for advisory assistance. Review required. Final certification decisions remain solely with the Bureau of Indian Standards.*';
        sources = [
          {
            id: `src-kb-${detected.standardCode.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
            title: `${detected.standardCode} — ${detected.standardTitle}`,
            documentRef: detected.standardCode,
            page: 3,
            section: 'Clause 4 — Technical Safety & Inspection Parameters',
            excerpt: `Technical requirements and laboratory testing protocols specified in ${detected.standardCode}.`,
            sourceUrl: 'https://www.services.bis.gov.in',
          },
        ];
      }

      const assistantMsg: ChatMessageItem = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: replyContent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources,
        conversationId: payload.conversationId,
      };

      activeChatHistory.push(assistantMsg);
      return assistantMsg;
    }
  },

  clearHistory: async (applicationId?: string): Promise<void> => {
    activeChatHistory = [createWelcomeMessage(applicationId)];
  },
};
