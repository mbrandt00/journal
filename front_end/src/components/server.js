import axios from "axios";
import { env } from "../env";

const instance = axios.create({
  baseURL: env.REACT_APP_SERVER_URL ?? process.env.REACT_APP_SERVER_URL,
  headers: { "Access-Control-Allow-Origin": "*" },
});
// const AxiosInterceptor = ({ children }) => {
//   const history = useHistory();
//   const { oktaAuth } = useOktaAuth();
//   useEffect(() => {
//     const reqInterceptor = (request) => {
//       if (!oktaAuth) {
//         return "Loading Authentiation";
//       } else {
//         request.headers["ID_TOKEN"] =
//           oktaAuth.authStateManager.getAuthState().idToken.idToken;
//         return request;
//       }
//     };

//     const resInterceptor = (response) => {
//       return response;
//     };
//     const errInterceptor = (error) => {
//       if (error.response.status === 404) {
//         history.push("/not_found");
//       } else if (error.response.status === 401) {
//         history.push("/unauthorized");
//       }
//       return Promise.reject(error);
//     };

//     const requestInterceptor = instance.interceptors.request.use(
//       reqInterceptor,
//       errInterceptor
//     );
//     const responseInterceptor = instance.interceptors.response.use(
//       resInterceptor,
//       errInterceptor
//     );
//     return () => {
//       instance.interceptors.request.eject(requestInterceptor);
//       instance.interceptors.response.eject(responseInterceptor);
//     };
//   }, []);

//   return children;
// };

export default instance;
// export { AxiosInterceptor };
