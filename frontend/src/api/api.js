import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8000'

export const searchRetailersApi = async (product, district) => {
  try {
    const response = await axios.get(
      `${BASE_URL}/search`,
      {
        params: {
          product,
          district
        }
      }
    )

    return response.data
  } catch (error) {
    console.error(error)
    return []
  }
}