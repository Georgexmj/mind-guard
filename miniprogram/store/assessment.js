import { defineStore } from 'pinia'

export const useAssessmentStore = defineStore('assessment', {
  state: () => ({
    currentSessionId: null,
    questions: [],
    currentQuestionIndex: 0,
    answers: [],
    taskId: null,
    result: null,
    sessionStartTime: null,
    questionStartTime: null
  }),

  getters: {
    currentQuestion: (state) => {
      if (state.questions.length === 0) return null
      return state.questions[state.currentQuestionIndex] || null
    },
    totalQuestions: (state) => state.questions.length,
    progress: (state) => {
      if (state.questions.length === 0) return 0
      return Math.round(((state.currentQuestionIndex) / state.questions.length) * 100)
    },
    isLastQuestion: (state) => {
      return state.currentQuestionIndex >= state.questions.length - 1
    },
    answeredCount: (state) => state.answers.length
  },

  actions: {
    /**
     * Start a new assessment session
     */
    startSession(sessionId) {
      this.currentSessionId = sessionId
      this.questions = []
      this.currentQuestionIndex = 0
      this.answers = []
      this.taskId = null
      this.result = null
      this.sessionStartTime = Date.now()
      this.questionStartTime = Date.now()
    },

    /**
     * Load questions for the session
     */
    setQuestions(questions) {
      this.questions = questions
      this.currentQuestionIndex = 0
      this.questionStartTime = Date.now()
    },

    /**
     * Record an answer for the current question and advance
     */
    submitAnswer(answer) {
      const reactionTime = Date.now() - (this.questionStartTime || Date.now())
      const fullAnswer = {
        ...answer,
        question_index: this.currentQuestionIndex,
        reaction_time_ms: reactionTime,
        timestamp: new Date().toISOString()
      }
      this.answers.push(fullAnswer)

      // Advance to next question
      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++
        this.questionStartTime = Date.now()
      }

      return fullAnswer
    },

    /**
     * Mark current question start time (call when question is displayed)
     */
    markQuestionStart() {
      this.questionStartTime = Date.now()
    },

    /**
     * Navigate to a specific question (used when returning from sub-tasks)
     */
    goToQuestion(index) {
      if (index >= 0 && index < this.questions.length) {
        this.currentQuestionIndex = index
        this.questionStartTime = Date.now()
      }
    },

    /**
     * Set the background task ID for AI analysis
     */
    setTaskId(taskId) {
      this.taskId = taskId
    },

    /**
     * Store the final result
     */
    setResult(result) {
      this.result = result
    },

    /**
     * Get reaction time in ms for current question
     */
    getReactionTime() {
      return Date.now() - (this.questionStartTime || Date.now())
    },

    /**
     * Reset all assessment state
     */
    reset() {
      this.currentSessionId = null
      this.questions = []
      this.currentQuestionIndex = 0
      this.answers = []
      this.taskId = null
      this.result = null
      this.sessionStartTime = null
      this.questionStartTime = null
    }
  }
})
