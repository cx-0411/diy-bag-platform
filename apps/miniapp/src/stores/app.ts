import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({ name: '包包刺绣 DIY 商城' }),
})
