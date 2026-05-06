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
      return Math.round(((state.currentQuestionIndex + 1) / state.questions.length) * 100)
    },
    isLastQuestion: (state) => state.currentQuestionIndex >= state.questions.length - 1,
    answeredCount: (state) => state.answers.length
  },

  actions: {
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
    setQuestions(questions) {
      this.questions = questions
      this.currentQuestionIndex = 0
      this.questionStartTime = Date.now()
    },
    submitAnswer(answer) {
      const reactionTime = Date.now() - (this.questionStartTime || Date.now())
      const fullAnswer = {
        ...answer,
        question_index: this.currentQuestionIndex,
        reaction_time_ms: reactionTime,
        timestamp: new Date().toISOString()
      }
      this.answers.push(fullAnswer)
      return fullAnswer
    },
    markQuestionStart() {
      this.questionStartTime = Date.now()
    },
    goToQuestion(index) {
      if (index >= 0 && index < this.questions.length) {
        this.currentQuestionIndex = index
        this.questionStartTime = Date.now()
      }
    },
    setTaskId(taskId) {
      this.taskId = taskId
    },
    setResult(result) {
      this.result = result
    },
    getReactionTime() {
      return Date.now() - (this.questionStartTime || Date.now())
    },
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